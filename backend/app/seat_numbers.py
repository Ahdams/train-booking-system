"""Convert the existing coach-based seat labels to unique numeric inventory IDs."""
import re

from fastapi import HTTPException


def normalize_seat_number(value: str, total_seats: int) -> str:
    seat = value.strip().upper()
    if seat.isdigit():
        number = int(seat)
    else:
        match = re.fullmatch(r"([1-3])-([A-D])([1-9][0-9]*)", seat)
        if match is None:
            raise HTTPException(status_code=400, detail="Invalid seat number")
        coach = int(match.group(1))
        column = ord(match.group(2)) - ord("A")
        row = int(match.group(3))
        index = (row - 1) * 4 + column + 1
        capacity = {1: 40, 2: 24, 3: 16}[coach]
        if index > capacity:
            raise HTTPException(status_code=400, detail="Seat exceeds coach capacity")
        number = {1: 0, 2: 40, 3: 64}[coach] + index
    if not 1 <= number <= total_seats:
        raise HTTPException(status_code=400, detail="Seat number must be within the train capacity")
    return str(number)
