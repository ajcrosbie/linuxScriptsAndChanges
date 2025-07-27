import argparse
import os
import json
from typing import Tuple, List
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Download, Page, BrowserContext, Cookie


def write_env(cookies_json: str, env_file: str = ".env") -> None:
    env_path = Path(env_file)

    # Remove the existing .env file if it exists
    if env_path.exists():
        try:
            env_path.unlink()
            print(f"Removed existing {env_file}")
        except Exception as e:
            raise RuntimeError(f"Failed to remove {env_file}: {e}")

    # Write the new .env file
    content = f"cookies={cookies_json}\n"
    env_path.write_text(content)
    print(f"Created fresh {env_file} with cookies.")

def ensure_cookies_in_env(env_file: str = ".env") -> str:
    """
    If missing or empty, launches browser login to retrieve cookies,
    updates the .env file, reloads environment variables,
    """

    cookies_json = retrieve_kudos_cookies()
    write_env(cookies_json,  env_file=env_file)

    # Reload updated environment variables
    load_dotenv(env_file, override=True)
    COOKIES_JSON = os.getenv("cookies")

    if COOKIES_JSON is None or COOKIES_JSON.strip() in ("", "[]"):
        raise EnvironmentError("Failed to load cookies even after retrieval.")

    return COOKIES_JSON

# === Utility Functions ===

def camel_case(text: str) -> str:
    """Converts space-separated text to camelCase."""
    return ''.join(word.capitalize() if i > 0 else word.lower() for i, word in enumerate(text.split()))


def get_kudos_details() -> Tuple[int, str]:
    """Extracts supervision number and subject name from the current directory path."""
    cwd: Path = Path.cwd()
    supo_number: int = int(cwd.name.replace("supo", ""))
    subject: str = cwd.parent.name
    return supo_number, subject


def update_tex_file(template_path: str) -> None:
    """Updates 'supo.tex' with template settings, writing to 'modifiedSupo.tex'."""
    input_file: Path = Path("supo.tex")
    output_file: Path = Path("modifiedSupo.tex")

    if not input_file.exists():
        raise FileNotFoundError("supo.tex not found in current directory.")

    content: str = input_file.read_text()

    if "\\documentclass{article}" not in content:
        raise ValueError("supo.tex does not contain a '\\documentclass{article}'")

    header_insert: str = (
        "\\input{infofile.tex}\n"
        "\\documentclass[10pt,\\jkfside,a4paper]{article}\n"
        f"\\input{{{template_path}}}"
    )

    new_content: str = content.replace("\\documentclass{article}", header_insert)
    output_file.write_text(new_content)

    print("Modified supo.tex written to 'modifiedSupo.tex'")



def retrieve_kudos_cookies() -> str:
    """
    Opens a browser for manual login to Kudos,
    captures cookies after login,
    and returns them as a JSON string.
    """
    print("Launching browser to log in and capture cookies...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto('https://kudos.chu.cam.ac.uk/login')
        page.click('a[alt="Login using the Raven web authentication system"]')

        # Wait for a URL that does NOT contain 'login' indicating successful login
        page.wait_for_url(lambda url: "kudos.chu.cam.ac.uk" in url and "login" not in url, timeout=600000)

        cookies = context.cookies()
        cookies_json = json.dumps(cookies)

        browser.close()
    return cookies_json


def download_correct_info_file(subject_name: str, supo_number: int, cookies: List[Cookie]) -> None:
    """Logs into Kudos and downloads the infofile.tex for the given subject and supervision."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context: BrowserContext = browser.new_context()
        context.add_cookies(cookies)
        page: Page = context.new_page()

        infofile_path: Path = Path.cwd() / "infofile.tex"

        def save_download(download: Download) -> None:
            download.save_as(str(infofile_path))
        page.on("download", save_download)

        print("Logging into Kudos")
        page.goto('https://kudos.chu.cam.ac.uk/login')
        page.click('a[alt="Login using the Raven web authentication system"]')
        page.wait_for_url('https://kudos.chu.cam.ac.uk/login', timeout=10000)

        print("Loading supo page")
        page.click('a.nav-link.dropdown-toggle:has-text("Supervisions")')
        page.click('a.dropdown-item:has-text("Booking")')
        page.wait_for_url('https://kudos.chu.cam.ac.uk/supervisions/booking', timeout=10000)
        page.wait_for_selector('thead.table-dark')

        print("Looking for matching supo")
        rows = page.query_selector_all('table tbody tr')

        for row in rows:
            subject_text: str = row.query_selector('td:nth-child(1)').inner_text()
            links = row.query_selector_all('td:nth-child(5) a')
            matching = [
                link for link in links
                if link.text_content() == f"SV#{supo_number + 1}"
            ]

            if camel_case(subject_name).lower() in camel_case(subject_text).lower() and matching:
                href: str | None = matching[0].get_attribute("href")
                if href:
                    page.click(f'a[href="{href}"]')
                    page.wait_for_event('download')
                    print("Download started.")
                break
        else:
            print("No matching supervision found.")

        browser.close()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=str(Path(__file__).parent / ".env"), help="Path to .env file")
    parser.add_argument("--template-path", required=True, help="Template path to write to .env")
    args = parser.parse_args()

    TEMPLATE_PATH = args.template_path

    COOKIES_JSON: str | None = os.getenv("cookies")

    if TEMPLATE_PATH is None:
        raise EnvironmentError("Missing 'templatePath' in environment variables.")

    if COOKIES_JSON is None:
        COOKIES_JSON = ensure_cookies_in_env(args.env_file)
        if not isinstance(COOKIES_JSON, str) or COOKIES_JSON.strip() in ("", "[]"):
            raise Exception("Cookies retrieval failed or returned empty content.")
        
    COOKIES: List[Cookie] = json.loads(COOKIES_JSON)

    supo_number, subject = get_kudos_details()

    if not Path("infofile.tex").exists():
        print("infofile.tex not found — downloading...")
        download_correct_info_file(subject, supo_number, COOKIES)
    else:
        print("infofile.tex already exists — skipping download.")

    update_tex_file(TEMPLATE_PATH)
