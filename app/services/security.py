from werkzeug.security import generate_password_hash, check_password_hash


def hash_pin(pin: str) -> str:
    return generate_password_hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    if not pin_hash:
        return False
    return check_password_hash(pin_hash, pin)
