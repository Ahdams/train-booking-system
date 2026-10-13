import bcrypt
import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.security import hash_password, verify_password


def test_existing_bcrypt_hash_remains_compatible():
    # An existing bcrypt-formatted hash can be checked without Passlib.
    legacy_hash = bcrypt.hashpw(b"ExistingPassword9!", bcrypt.gensalt(rounds=12)).decode("ascii")
    assert verify_password("ExistingPassword9!", legacy_hash)
    assert not verify_password("WrongPassword9!", legacy_hash)


def test_new_password_hash_roundtrip():
    stored = hash_password("NewPassword9!")
    assert stored.startswith("$2b$12$")
    assert verify_password("NewPassword9!", stored)
    assert not verify_password("WrongPassword9!", stored)


def test_unicode_password_roundtrip():
    stored = hash_password("Securé🔒Password9!")
    assert verify_password("Securé🔒Password9!", stored)


def test_malformed_hash_rejected():
    assert not verify_password("Password9!", "not-a-bcrypt-hash")


def test_password_longer_than_72_utf8_bytes_is_rejected():
    with pytest.raises(ValueError):
        hash_password("a" * 73)
    assert not verify_password("a" * 73, hash_password("a" * 72))
    with pytest.raises(ValidationError):
        RegisterRequest(full_name="Test User", email="long@example.com", password="🔒" * 19)


def test_72_byte_password_works():
    password = "a" * 72
    assert verify_password(password, hash_password(password))
