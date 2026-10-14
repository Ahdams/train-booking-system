import pytest
from fastapi import HTTPException
from app.seat_numbers import normalize_seat_number

@pytest.mark.parametrize("label,expected", [("1-A1","1"),("1-D10","40"),("2-A1","41"),("2-D6","64"),("3-A1","65"),("3-D4","80"),("2-B3","50"),("080","80")])
def test_coach_seat_mapping(label, expected):
    assert normalize_seat_number(label, 80) == expected

@pytest.mark.parametrize("label", ["1-A11","2-A7","3-A5","4-A1","1-E1","1-A0","0","81"])
def test_invalid_seat(label):
    with pytest.raises(HTTPException) as exc:
        normalize_seat_number(label, 80)
    assert exc.value.status_code == 400

def test_numeric_alias_matches_coach_label():
    assert normalize_seat_number("1-A1",80) == normalize_seat_number("1",80)

def test_train_capacity_limit():
    with pytest.raises(HTTPException):
        normalize_seat_number("2-A1",10)
