import uuid

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def enable_test_wallet_funding(monkeypatch):
    monkeypatch.setattr(settings, "enable_dev_wallet_credit", True)


def unique_email() -> str:
    return f"ci-{uuid.uuid4().hex}@example.com"


def register_user(email: str | None = None) -> tuple[str, str]:
    email = email or unique_email()
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "CI Test User",
            "email": email,
            "password": "CorrectHorseBattery9!",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"], email


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    token, email = register_user()
    assert token
    response = client.post(
        "/api/auth/login",
        json={"email": email.upper(), "password": "CorrectHorseBattery9!"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_duplicate_registration_is_rejected():
    _, email = register_user()
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Duplicate User",
            "email": email,
            "password": "CorrectHorseBattery9!",
        },
    )
    assert response.status_code == 409


def test_wallet_requires_authentication():
    response = client.get("/api/wallet")
    assert response.status_code == 401


def test_non_admin_cannot_access_admin_dashboard():
    token, _ = register_user()
    response = client.get("/api/admin/dashboard", headers=auth(token))
    assert response.status_code == 403


def test_admin_dashboard_requires_authentication():
    response = client.get("/api/admin/dashboard")
    assert response.status_code == 401


def test_users_only_see_their_own_reports():
    token_a, _ = register_user()
    token_b, _ = register_user()

    created = client.post(
        "/api/reports",
        headers=auth(token_a),
        json={"subject": "CI report A", "description": "Report belonging to test user A"},
    )
    assert created.status_code == 201, created.text

    reports_a = client.get("/api/reports/mine", headers=auth(token_a))
    reports_b = client.get("/api/reports/mine", headers=auth(token_b))
    assert reports_a.status_code == 200
    assert reports_b.status_code == 200
    assert any(item["subject"] == "CI report A" for item in reports_a.json())
    assert all(item["subject"] != "CI report A" for item in reports_b.json())


def test_wallet_transactions_are_account_specific():
    token_a, _ = register_user()
    token_b, _ = register_user()

    credit = client.post(
        "/api/wallet/credit",
        headers=auth(token_a),
        json={
            "amount": "12.50",
            "idempotency_key": f"ci-{uuid.uuid4().hex}",
            "description": "CI test credit",
        },
    )
    assert credit.status_code == 201, credit.text

    history_a = client.get("/api/wallet/transactions", headers=auth(token_a))
    history_b = client.get("/api/wallet/transactions", headers=auth(token_b))
    assert history_a.status_code == 200
    assert history_b.status_code == 200
    assert any(item["description"] == "CI test credit" for item in history_a.json())
    assert all(item["description"] != "CI test credit" for item in history_b.json())


def test_wallet_credit_idempotency_returns_existing_transaction():
    token, _ = register_user()
    key = f"ci-{uuid.uuid4().hex}"
    payload = {
        "amount": "7.25",
        "idempotency_key": key,
        "description": "Idempotency test",
    }
    first = client.post("/api/wallet/credit", headers=auth(token), json=payload)
    second = client.post("/api/wallet/credit", headers=auth(token), json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] == second.json()["id"]

    wallet = client.get("/api/wallet", headers=auth(token))
    assert wallet.status_code == 200
    assert str(wallet.json()["balance"]) == "7.25"


def test_non_admin_cannot_list_all_reports():
    token, _ = register_user()
    response = client.get("/api/reports", headers=auth(token))
    assert response.status_code == 403


def test_non_admin_cannot_resolve_a_report():
    token, _ = register_user()
    response = client.patch(
        "/api/reports/999999/resolve",
        headers=auth(token),
        json={"admin_response": "Reviewed by admin"},
    )
    assert response.status_code == 403


def test_train_search_rejects_same_origin_and_destination():
    response = client.get(
        "/api/trains/search",
        params={"origin_station_id": 1, "destination_station_id": 1},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Origin and destination must be different"


def test_booking_requires_authentication():
    response = client.post("/api/bookings", json={
        "schedule_id": 1, "travel_date": "2099-01-01", "seat_number": "1"
    })
    assert response.status_code == 401


def test_schedule_creation_requires_admin():
    token, _ = register_user()
    response = client.post("/api/schedules", headers=auth(token), json={
        "train_id": 1, "origin_station_id": 1, "destination_station_id": 2,
        "departure_time": "09:00:00", "arrival_time": "10:00:00",
        "operating_days": ["Mon"], "fare": "5000.00"
    })
    assert response.status_code == 403


def test_schedule_fare_must_be_positive():
    from pydantic import ValidationError
    from app.schemas.schedule import ScheduleCreate, ScheduleFareUpdate

    payload = {
        "train_id": 1, "origin_station_id": 1, "destination_station_id": 2,
        "departure_time": "09:00:00", "arrival_time": "10:00:00",
        "operating_days": ["Mon"], "fare": "-100.00"
    }
    with pytest.raises(ValidationError):
        ScheduleCreate.model_validate(payload)
    with pytest.raises(ValidationError):
        ScheduleFareUpdate.model_validate({"fare": "-100.00"})


def setup_paid_schedule(fare="5000.00"):
    from datetime import date, timedelta
    from decimal import Decimal
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import Schedule, Station, Train

    tag = uuid.uuid4().hex[:10].upper()
    travel_date = date.today() + timedelta(days=7)
    with SessionLocal() as db:
        origin = Station(name=f"Origin {tag}", code=f"O{tag}")
        destination = Station(name=f"Destination {tag}", code=f"D{tag}")
        train = Train(name=f"CI Train {tag}", train_number=f"CI-{tag}", total_seats=10)
        db.add_all([origin, destination, train])
        db.flush()
        schedule = Schedule(
            train_id=train.id, origin_station_id=origin.id,
            destination_station_id=destination.id,
            departure_time=__import__("datetime").time(9, 0),
            arrival_time=__import__("datetime").time(10, 0),
            operating_days="Mon,Tue,Wed,Thu,Fri,Sat,Sun",
            status="active", fare=Decimal(fare),
        )
        db.add(schedule)
        db.commit()
        return schedule.id, travel_date.isoformat()


def fund_wallet(token, amount):
    response = client.post("/api/wallet/credit", headers=auth(token), json={
        "amount": amount,
        "idempotency_key": f"ci-{uuid.uuid4().hex}",
        "description": "CI test funding",
    })
    assert response.status_code == 201, response.text


def make_test_admin(email):
    from sqlalchemy import select
    from app.database import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        user.is_admin = True
        db.commit()


def test_paid_booking_deducts_fare_and_records_transaction():
    schedule_id, travel_date = setup_paid_schedule()
    token, _ = register_user()
    fund_wallet(token, "8000.00")
    booking = client.post("/api/bookings", headers=auth(token), json={
        "schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1"
    })
    assert booking.status_code == 201, booking.text
    assert str(booking.json()["amount"]) == "5000.00"
    wallet = client.get("/api/wallet", headers=auth(token))
    assert str(wallet.json()["balance"]) == "3000.00"
    history = client.get("/api/wallet/transactions", headers=auth(token))
    assert history.status_code == 200
    assert len([t for t in history.json() if t["booking_id"] == booking.json()["id"] and t["transaction_type"] == "debit"]) == 1


def test_insufficient_balance_does_not_create_booking():
    schedule_id, travel_date = setup_paid_schedule()
    token, _ = register_user()
    fund_wallet(token, "1000.00")
    response = client.post("/api/bookings", headers=auth(token), json={
        "schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1"
    })
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Insufficient wallet balance"
    assert client.get("/api/bookings/mine", headers=auth(token)).json() == []
    assert str(client.get("/api/wallet", headers=auth(token)).json()["balance"]) == "1000.00"


def test_duplicate_seat_does_not_charge_second_passenger():
    schedule_id, travel_date = setup_paid_schedule()
    first_token, _ = register_user()
    second_token, _ = register_user()
    fund_wallet(first_token, "5000.00")
    fund_wallet(second_token, "5000.00")
    payload = {"schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1"}
    first = client.post("/api/bookings", headers=auth(first_token), json=payload)
    second = client.post("/api/bookings", headers=auth(second_token), json=payload)
    assert first.status_code == 201, first.text
    assert second.status_code == 409, second.text
    assert str(client.get("/api/wallet", headers=auth(second_token)).json()["balance"]) == "5000.00"
    assert client.get("/api/bookings/mine", headers=auth(second_token)).json() == []


def test_admin_cancellation_refunds_once_and_releases_seat():
    schedule_id, travel_date = setup_paid_schedule()
    passenger_token, _ = register_user()
    admin_token, admin_email = register_user()
    make_test_admin(admin_email)
    fund_wallet(passenger_token, "5000.00")
    payload = {"schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1"}
    created = client.post("/api/bookings", headers=auth(passenger_token), json=payload)
    assert created.status_code == 201, created.text
    booking_id = created.json()["id"]
    endpoint = f"/api/bookings/{booking_id}/status"
    first = client.patch(endpoint, headers=auth(admin_token), json={"status": "cancelled"})
    second = client.patch(endpoint, headers=auth(admin_token), json={"status": "cancelled"})
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert str(client.get("/api/wallet", headers=auth(passenger_token)).json()["balance"]) == "5000.00"
    history = client.get("/api/wallet/transactions", headers=auth(passenger_token)).json()
    assert len([t for t in history if t["booking_id"] == booking_id and t["transaction_type"] == "refund"]) == 1
    another_token, _ = register_user()
    fund_wallet(another_token, "5000.00")
    replacement = client.post("/api/bookings", headers=auth(another_token), json=payload)
    assert replacement.status_code == 201, replacement.text


def test_booking_payment_is_private_to_passenger():
    schedule_id, travel_date = setup_paid_schedule()
    owner_token, _ = register_user()
    other_token, _ = register_user()
    fund_wallet(owner_token, "5000.00")
    booked = client.post("/api/bookings", headers=auth(owner_token), json={
        "schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "2"
    })
    assert booked.status_code == 201, booked.text
    booking_id = booked.json()["id"]
    assert client.get(f"/api/bookings/{booking_id}", headers=auth(other_token)).status_code == 403
    assert all(t["booking_id"] != booking_id for t in client.get("/api/wallet/transactions", headers=auth(other_token)).json())


def test_development_wallet_credit_is_disabled_by_default(monkeypatch):
    token, _ = register_user()
    monkeypatch.setattr(settings, "enable_dev_wallet_credit", False)
    response = client.post("/api/wallet/credit", headers=auth(token), json={
        "amount": "1000.00",
        "idempotency_key": f"ci-{uuid.uuid4().hex}",
        "description": "Must not be credited",
    })
    assert response.status_code == 403
    assert str(client.get("/api/wallet", headers=auth(token)).json()["balance"]) == "0.00"


def test_simultaneous_booking_requests_only_charge_one_passenger():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    schedule_id, travel_date = setup_paid_schedule()
    first_token, _ = register_user()
    second_token, _ = register_user()
    fund_wallet(first_token, "5000.00")
    fund_wallet(second_token, "5000.00")
    payload = {"schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "3"}
    barrier = Barrier(2)

    def attempt(token):
        barrier.wait(timeout=10)
        with TestClient(app) as concurrent_client:
            return concurrent_client.post("/api/bookings", headers=auth(token), json=payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, token) for token in (first_token, second_token)]
        results = [future.result(timeout=20) for future in futures]

    assert sorted(response.status_code for response in results) == [201, 409], [
        (response.status_code, response.text) for response in results
    ]
    balances = [
        str(client.get("/api/wallet", headers=auth(token)).json()["balance"])
        for token in (first_token, second_token)
    ]
    assert sorted(balances) == ["0.00", "5000.00"]
    assert sum(len(client.get("/api/bookings/mine", headers=auth(token)).json()) for token in (first_token, second_token)) == 1
