import requests

def github_blob_to_raw(url: str) -> str:
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url

def fetch_github_code(url: str, remove_comments: bool = False) -> str:
    """
    Fetches raw github code from the given url and returns it.

    :param url: url to public github code
    :param remove_comments: Decide whether to remove comments
    :return: string with raw github code
    """
    raw_url = github_blob_to_raw(url)
    try:
        resp = requests.get(raw_url, timeout=10)
        if resp.status_code != 200:
            return f"# Failed to fetch code (status {resp.status_code})"

        code = resp.text
        if remove_comments:
            code = strip_comments(code)
        return code

    except Exception as e:
        return f"# Error fetching code: {e}"

def strip_comments(code: str) -> str:
    """
    Remove comments from Python code.

    - Removes lines starting with #
    - Removes inline # comments
    """
    no_hash = []
    for line in code.splitlines():
        # Remove full-line comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Remove inline comments
        if "#" in line:
            line = line.split("#", 1)[0].rstrip()
        no_hash.append(line)
    return "\n".join(no_hash)
