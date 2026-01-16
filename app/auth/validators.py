import re


# --------------------------------------------------
# EMAIL VALIDATION
# --------------------------------------------------
def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


# --------------------------------------------------
# PASSWORD STRENGTH VALIDATION
# --------------------------------------------------
def is_strong_password(password: str) -> bool:
    """
    Rules:
    - min 6 characters
    - at least 1 uppercase
    - at least 1 number
    """
    if len(password) < 6:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True
