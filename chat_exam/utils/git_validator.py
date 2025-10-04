import re
import requests

def check_github_link(url: str) -> tuple[bool, str]:
    """
    Validate if a string is a valid GitHub link and check if it exists.
    Returns (ok, message).
    """
    if not url:
        return False, "No link provided"

    # Regex for github.com/user/repo or deeper
    pattern = re.compile(
        r"^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(\/.*)?$"
    )
    if not pattern.match(url):
        return False, "Not a valid GitHub URL format"

    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return True, "Valid and reachable"
        elif response.status_code == 404:
            return False, "GitHub link not found (404)"
        else:
            return False, f"GitHub returned {response.status_code}"
    except requests.RequestException as e:
        return False, f"Request failed: {e}"
