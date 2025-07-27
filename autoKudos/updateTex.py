from playwright.sync_api import sync_playwright
import os
from collections.abc import Callable
from dotenv import load_dotenv
import json

load_dotenv()
templatePath = os.getenv("templatePath") # this includes template.tex
cookies = os.getenv("cookies")

cookies = json.loads(cookies)
def getKudosDetails():
    cwd = os.getcwd()
    parent_dir = os.path.basename(os.path.dirname(cwd))
    return int(os.path.basename(cwd).replace("supo", "")), parent_dir


def updateTex():
    if not os.path.isfile("supo.tex"):
        raise FileExistsError("no supo in CWD")
    with open("supo.tex") as f:
        tex = f.read()
    if not "\\documentclass{article}" in tex:
        raise ValueError("supo.tex does not contain a \\documentclass{article}")


    s = """\\input{infofile.tex}
\\documentclass[10pt,\\jkfside,a4paper]{article}
\\input{""" + templatePath + "}"


    with open("modifiedSupo.tex", "w") as f:
        f.write(tex.replace("\\documentclass{article}", s))
    print("modified supo created")


def getCookiesToFile():
    with sync_playwright() as p:
        # Launch a Chromium browser
        browser = p.chromium.launch(headless=False)  # Set headless=False to see the browser
        page = browser.new_page()
        
        # Navigate to a webpage
        page.goto('https://kudos.chu.cam.ac.uk/login')
        
        # Take a screenshot
        page.click('a[alt="Login using the Raven web authentication system"][title="Login using the Raven web authentication system"]')
        page.wait_for_url('https://kudos.chu.cam.ac.uk/login', timeout=1000000)

        # Close the browser
        cookies= page.context.cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        
        browser.close()
    
def downloadCorrectInfoFile(subjectName:str, supoNumber:int):
    with sync_playwright() as p:
        # Launch a Chromium browser
        browser = p.chromium.launch(headless=True)  # Set headless=False to see the browser
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        download_path = os.path.join(os.getcwd(), "infofile.tex")  # Specify the full path
        page.on("download", lambda d: d.save_as(download_path))

        # Navigate to a webpage
        page.goto('https://kudos.chu.cam.ac.uk/login')
        print("logging into kudos")

        # Take a screenshot
        page.click('a[alt="Login using the Raven web authentication system"][title="Login using the Raven web authentication system"]')
        page.wait_for_url('https://kudos.chu.cam.ac.uk/login', timeout=10000)
        print("logged into kudos")
        page.click('a.nav-link.dropdown-toggle:has-text("Supervisions")')
        page.click('a.dropdown-item:has-text("Booking")')
        print("loading supos page")
        page.wait_for_url('https://kudos.chu.cam.ac.uk/supervisions/booking', timeout=10000)
        page.wait_for_selector('thead.table-dark')
        print("loaded supos page")
        page.screenshot(path="ex2.png")


        rows = page.query_selector_all('table tbody tr')
        for row in rows:
            column_1_text = row.query_selector('td:nth-child(1)').inner_text()
            links_in_column_5 = row.query_selector_all('td:nth-child(5) a')  # All links in column 3
           # Filter the links in column 5 that match the desired text
            matching_links = [link for link in links_in_column_5 if link.text_content() == f"SV#{supoNumber+1}"]
            # If the subject name matches the one in the first column
            if camelCase(subjectName).lower() in camelCase(column_1_text).lower() and matching_links:
                # Click the first matching link in column 5
                absolute_url = matching_links[0].get_attribute("href")
                page.click(f'a[href="{absolute_url}"]')
                page.wait_for_event('download')
            
        browser.close()

camelCase :Callable[[str], str] = lambda string_with_spaces:''.join(word.capitalize() if i > 0 else word.lower() for i, word in enumerate(string_with_spaces.split()))

if __name__ == "__main__":
    supNum, subj = getKudosDetails()
    
    if not os.path.isfile("infofile.tex"):
        print("infofile.tex not found — downloading...")
        downloadCorrectInfoFile(subj, supNum)
    else:
        print("infofile.tex already exists — skipping download.")
    
    updateTex()