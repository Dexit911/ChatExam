# === Base ===
import re
import requests
from pathlib import Path
# === Local ===
from chat_exam.exceptions import RequestError, TimeoutError, AppError, EmptyRepo
from chat_exam.config import Config

# === TOKEN ===

TOKEN = Config.GITHUB_FETCH_TOKEN
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def github_blob_to_raw(url: str) -> str:
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return url


def fetch_github_code(url: str, remove_comments: bool = False) -> str:
    """
    Fetches raw gitHub code from the given url and returns it.

    :param url: url to public gitHub code
    :param remove_comments: Decide whether to remove comments
    :return: string with raw gitHub code
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


# === Fetch for repo ===
def fetch_github_repo(url: str, max_files: int, remove_comments: bool = True) -> dict:
    """
    Fetches allowed code from the given gitHub repo url and returns it.

    :param url: (str) url to public gitHub repo
    :param max_files: (int) max number of allowed files that's going to show in exam
    :param remove_comments: (bool) whether to remove comments

    :return: (dict) with filtered data that is going to be passed to template
    """

    try:
        # === Request response ===
        api_url = _repo_to_api(url)
        res = requests.get(api_url, headers=HEADERS, timeout=8)

        try:
            api_res = res.json()
        except ValueError:
            raise AppError("Invalid response from GitHub.", public=True)

        # === Check if there is any content in repo ===
        if not isinstance(api_res, list):
            raise EmptyRepo(public=True)

        # === Instructions for filter data, should be editable ===
        instructions = {
            ".html": ["index.html", "base.html", "main.html"],
            ".css": ["index.css", "base.css", "main.css", "style.css"],
        }

        # === Get data that passes the filter instructions ===
        data = _get_allowed_data(instructions, api_res, max_files) # Main files
        data = _get_connected_html_files(data, url, max_files) # Main file + files connected to main .html file


        # === Remove comments if needed ===
        if remove_comments:
            data = _remove_comments(data, url)

        # === Return dict ready for monaco code viewer ===
        return data

    # === If internet drops ===
    except requests.exceptions.Timeout:
        raise TimeoutError("GitHub didn’t respond in time. Please try again later.", public=True)

    except Exception as e:
        raise AppError(f"Unexpected internal error: {e}", public=False)


def _remove_comments(code: dict | str, filename=None) -> dict:
    """
    Recursive functions that handles both dict and str.

    Removes comments from fetched files - remove logic is based on file extension.
    :param code: (dict|str) code to remove comments from
    :param filename: (str) filename of the code. Extensions decides what remove logic to use.
    :return: dict with code with strict comment that is ready for monaco viewer.
             Example on returned dict:
        {
            "index.html": "<"<!DOCTYPE html> ...",
            "style.css": "body {...} ...",
        }
    """
    # === Handle dict output ===
    if isinstance(code, dict):
        return {name: _remove_comments(text, name) for name, text in code.items()}

    #  === Handle string output ===
    extension = Path(filename or "").suffix.lower()

    match extension:
        case ".py":
            lines = []
            for line in code.splitlines():
                # Remove full-line comments
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Remove inline comments
                if "#" in line:
                    line = line.split("#", 1)[0].rstrip()
                lines.append(line)
            return "\n".join(lines)

        case ".js" | ".css" | ".java" | ".c" | ".cpp":
            code = re.sub(r"//.*", "", code)
            code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
            return code

        case ".html":
            return re.sub(r"<!--.*?-->", "", code, flags=re.S)

        # If extension did not match any extensions above, or its none return nothing
        case _:
            return code


def _repo_to_api(repo_url: str) -> str:
    """
    Converts the given url to an api contents url
    : param repo_url: (str) gitHub repo url
    """
    parts = repo_url.rstrip('/').split('/')
    user, repo = parts[-2], parts[-1]
    return f"https://api.github.com/repos/{user}/{repo}/contents/"


def _get_allowed_data(instructions: dict, api_res: list, max_files: int) -> dict:
    """
    Get allowed data from given instructions
    :param instructions: (dict) instructions- example:
        {
            ".html": ["index.html", "base.html", "main.html"],
            ".css": ["index.css", "base.css", "main.css", "style.css"],
            ...
        }

    :param api_res: (dict) response from gitHub api - example:
        [
            {
                "name": "index.html",
                "path": "index.html",
                "sha": "f9f8b90f2d2e7f...",
                "size": 512,
                and a lot more...,
            },
            ...
        ]

    :return: (dict) with allowed data. It's ready to be putted in monaco editor
             or be applied with _remove_comments().
             Example on returned dict:
        {
            "index.html": "<"<!DOCTYPE html> ...",
            "style.css": "body {...} ...",
            ...
        }
    """

    # === Create a list with allowed file extensions ===
    allowed = list(instructions.keys())

    # === Filter allowed files adn put them in a list ===
    files = []
    for f in api_res:
        name = f["name"].lower()
        ext = Path(name).suffix

        if ext in allowed:
            files.append(f)

        if len(files) >= max_files:
            break

        if f.get("type") != "file" or "download_url" not in f:
            continue # skip dirs

    # === Create dict with format that is ready to be passed in template ===
    data = {f["name"]: requests.get(f["download_url"]).text for f in files}

    return data


def _get_connected_html_files(data: dict, base_url: str, max_files: int) -> dict:
    """
    Fetch .html files linked from the main HTML file only.

    :param data: (dict) in format that (func) _get_allowed_data(...) returns
    :param base_url: (str) gitHub repo url
    :param max_files: (int) maximum number of files to fetch

    :return data: (dict) allowed data + connected html files
    """
    # === Do nothing if no data provided ===
    if not data:
        return data

    # === The only .html file from base data ===
    main_name = next((n for n in data if n.endswith(".html")), None)

    # === Do nothing if no data ===
    if not main_name:
        return data

    # === Look for links to other files in main .html file ===
    main_html = data[main_name]
    linked = re.findall(r'href=["\']([^"\']+\.html)["\']', main_html)
    new_files = {}

    # === Try to fetch data from linked files, if succeed - store file content ===
    for href in linked[:max_files - len(data)]:
        raw_url = base_url.rstrip("/") + "/" + href.lstrip("/")
        try:
            resp = requests.get(raw_url, timeout=8)
            if resp.status_code == 200:
                new_files[href] = resp.text
        except Exception:
            continue

    # === Add all stored file content to main data and return it ===
    data.update(new_files)
    return data




