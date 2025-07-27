import os
import json
from typing import Tuple, List
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Download, Page, BrowserContext, Cookie

# Load environment variables
load_dotenv()

TEMPLATE_PATH: str | None = os.getenv("templatePath")
COOKIES_JSON: str | None = os.getenv("cookies")

if TEMPLATE_PATH is None:
    raise EnvironmentError("Missing 'templatePath' in environment variables.")
if COOKIES_JSON is None:
    raise EnvironmentError("Missing 'cookies' in environment variables.")

COOKIES: List[Cookie] = json.loads(COOKIES_JSON)


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


def get_cookies_to_file() -> None:
    """Interactively logs in and saves session cookies to 'cookies.json'."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page: Page = browser.new_page()

        page.goto('https://kudos.chu.cam.ac.uk/login')
        page.click('a[alt="Login using the Raven web authentication system"]')
        page.wait_for_url('https://kudos.chu.cam.ac.uk/login', timeout=600000)

        cookies: List[Cookie] = page.context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)

        print("Cookies saved to 'cookies.json'")
        browser.close()


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


# === Entry Point ===

if __name__ == "__main__":
    supo_number, subject = get_kudos_details()

    if not Path("infofile.tex").exists():
        print("infofile.tex not found — downloading...")
        download_correct_info_file(subject, supo_number, COOKIES)
    else:
        print("infofile.tex already exists — skipping download.")

    update_tex_file(TEMPLATE_PATH)
