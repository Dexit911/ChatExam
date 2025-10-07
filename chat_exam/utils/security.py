from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password: str) -> str:
    """Hash a plain password with a secure algorithm."""
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Check if a plain password matches the hashed one."""
    return check_password_hash(hashed, password)