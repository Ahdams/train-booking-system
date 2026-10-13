import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
    token, _ = register_user()
    response = client.post("/api/schedules", headers=auth(token), json={
        "train_id": 1, "origin_station_id": 1, "destination_station_id": 2,
        "departure_time": "09:00:00", "arrival_time": "10:00:00",
        "operating_days": ["Mon"], "fare": "-100.00"
    })
    assert response.status_code == 422
