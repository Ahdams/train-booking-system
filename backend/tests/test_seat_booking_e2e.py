"""API integration: two accounts cannot reserve one physical seat under different labels."""
from test_api import client, register_user, auth, setup_paid_schedule, fund_wallet


def test_coach_label_and_numeric_alias_share_booking_inventory():
    schedule_id, travel_date = setup_paid_schedule()
    token_a, _ = register_user()
    token_b, _ = register_user()
    fund_wallet(token_a, "8000.00")
    fund_wallet(token_b, "8000.00")

    first = client.post("/api/bookings", headers=auth(token_a), json={
        "schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1-A1"
    })
    second = client.post("/api/bookings", headers=auth(token_b), json={
        "schedule_id": schedule_id, "travel_date": travel_date, "seat_number": "1"
    })

    assert first.status_code == 201, first.text
    assert first.json()["seat_number"] == "1"
    assert second.status_code == 409, second.text
    wallet = client.get("/api/wallet", headers=auth(token_b))
    assert wallet.status_code == 200
    assert wallet.json()["balance"] == "8000.00"
