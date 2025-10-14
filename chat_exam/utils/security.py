from werkzeug.security import generate_password_hash, check_password_hash


"""PASSWORD HASHING"""
def hash_password(password: str) -> str:
    """Hash a plain password with a secure algorithm."""
    return generate_password_hash(password)

def verify_password(password: str, hashed: str) -> bool:
    """Check if a plain password matches the hashed one."""
    return check_password_hash(hashed, password)

"""DETECT SEB ENV REQUEST"""
def is_seb_request(req):
    return (
        "X-SafeExamBrowser-ConfigKeyHash" in req.headers
        or "X-SafeExamBrowser-RequestHash" in req.headers
    )
