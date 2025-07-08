# file: auth_utils.py
import bcrypt


def hash_password(password: str) -> bytes:
    """رمز عبور را به صورت امن هش می‌کند."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password


def check_password(password: str, hashed_password: bytes) -> bool:
    """بررسی می‌کند که آیا رمز عبور وارد شده با هش ذخیره شده مطابقت دارد یا خیر."""
    password_bytes = password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password)
