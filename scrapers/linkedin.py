import os
import sys
import json
import time
import random
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

from dotenv import load_dotenv
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------------------ Config ---------------------------------

DEFAULT_TIMEOUT = 15
SCROLL_PAUSE = (0.6, 1.1)   # random.uniform(*SCROLL_PAUSE)
SECTION_TIMEOUT = 5

# ------------------------------ Models ---------------------------------

@dataclass
class ExperienceItem:
    title: Optional[str] = None
    company: Optional[str] = None
    date_range: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

@dataclass
class EducationItem:
    school: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    date_range: Optional[str] = None
    description: Optional[str] = None

@dataclass
class ProfileData:
    url: str = ""
    name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    experiences: List[ExperienceItem] = None
    education: List[EducationItem] = None
    skills: List[str] = None
    websites: List[str] = None
    email: Optional[str] = None

# ------------------------------ Utils ----------------------------------

def randsleep(a, b):
    time.sleep(random.uniform(a, b))

def get_text(el) -> Optional[str]:
    try:
        txt = el.text.strip()
        return txt if txt else None
    except Exception:
        return None

def safe_find(driver, by, value, timeout=SECTION_TIMEOUT):
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except Exception:
        return None

def safe_find_all(driver, by, value, timeout=SECTION_TIMEOUT):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        return driver.find_elements(by, value)
    except Exception:
        return []

def click_if_present(driver, by, value, timeout=3):
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False

def scroll_page(driver, steps=6):
    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight/6);")
        randsleep(*SCROLL_PAUSE)

def scroll_to_element(driver, el):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        randsleep(0.3, 0.7)
    except Exception:
        pass

def find_section_by_heading(driver, heading_text: str):
    """
    Find a section container by H2 heading text like 'About', 'Experience', 'Education', 'Skills'.
    Uses a fuzzy contains() selector to survive minor copy changes.
    """
    xpath = f"//section[.//h2[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{heading_text.lower()}')]]"
    el = safe_find(driver, By.XPATH, xpath, timeout=3)
    return el

def expand_all_see_more_in_section(section_el, driver):
    try:
        buttons = section_el.find_elements(By.XPATH, ".//button[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'see more') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'show more')]]")
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                randsleep(0.2, 0.5)
            except Exception:
                pass
    except Exception:
        pass

# ------------------------------ Scrapers --------------------------------

def extract_header(driver: webdriver.Chrome, data: ProfileData):
    """
    Header typically has name, headline, and location near the top.
    """
    # Name (h1)
    h1 = safe_find(driver, By.TAG_NAME, "h1", timeout=DEFAULT_TIMEOUT)
    data.name = get_text(h1)

    # Headline: often in a div near name with class 'text-body-medium break-words'
    headline = safe_find(driver, By.CSS_SELECTOR, "div.text-body-medium.break-words", timeout=5)
    data.headline = get_text(headline)

    # Location: small 'text-body-small' near headline
    loc = safe_find(driver, By.XPATH, "//div[contains(@class,'mt2')]//span[contains(@class,'text-body-small')]", timeout=5)
    data.location = get_text(loc)

def extract_about(driver: webdriver.Chrome, data: ProfileData):
    sec = find_section_by_heading(driver, "About")
    if not sec:
        return
    scroll_to_element(driver, sec)
    expand_all_see_more_in_section(sec, driver)
    # The about text is often inside <div> with 'inline-show-more-text' or similar
    about_el = safe_find(sec, By.XPATH, ".//div[contains(@class,'inline-show-more-text') or contains(@class,'display-flex') or contains(@class,'break-words')]")
    data.about = get_text(about_el)

def extract_experience(driver: webdriver.Chrome, data: ProfileData):
    sec = find_section_by_heading(driver, "Experience")
    data.experiences = []
    if not sec:
        return

    scroll_to_element(driver, sec)
    expand_all_see_more_in_section(sec, driver)

    # Each experience "li" entry
    items = sec.find_elements(By.XPATH, ".//li[.//div[contains(@class,'display-flex')]]")
    for item in items:
        try:
            exp = ExperienceItem()
            # Title: first strong tag or span with class
            title = item.find_elements(By.XPATH, ".//span[contains(@class,'mr1')]/span|.//div[contains(@class,'t-bold')]/span|.//a//div[contains(@class,'t-bold')]/span")
            if title:
                exp.title = get_text(title[0])

            # Company: next line or t-normal span
            company = item.find_elements(By.XPATH, ".//span[contains(@class,'t-normal')]/span|.//span[contains(@class,'t-14 t-normal')]/span")
            if company:
                exp.company = get_text(company[0])

            # Date range and location are commonly small text rows
            date_row = item.find_elements(By.XPATH, ".//span[contains(@class,'t-14 t-normal t-black--light')]/span|.//span[contains(@class,'t-14 t-normal t-black--light')]")
            if date_row:
                # Heuristic: first small row is dates, second might be location
                exp.date_range = get_text(date_row[0]) if len(date_row) >= 1 else None
                exp.location   = get_text(date_row[1]) if len(date_row) >= 2 else None

            # Description may appear after expanding
            desc = item.find_elements(By.XPATH, ".//div[contains(@class,'inline-show-more-text') or contains(@class,'show-more-less-text')]")
            if desc:
                exp.description = get_text(desc[0])

            # Only keep non-empty
            if any([exp.title, exp.company, exp.date_range, exp.location, exp.description]):
                data.experiences.append(exp)
        except Exception:
            continue

def extract_education(driver: webdriver.Chrome, data: ProfileData):
    sec = find_section_by_heading(driver, "Education")
    data.education = []
    if not sec:
        return

    scroll_to_element(driver, sec)
    expand_all_see_more_in_section(sec, driver)

    items = sec.find_elements(By.XPATH, ".//li[.//div[contains(@class,'display-flex')]]")
    for item in items:
        try:
            edu = EducationItem()
            school = item.find_elements(By.XPATH, ".//span[contains(@class,'mr1')]/span|.//div[contains(@class,'t-bold')]/span")
            if school:
                edu.school = get_text(school[0])

            # degree + field often appear in the next spans
            degree_field = item.find_elements(By.XPATH, ".//span[contains(@class,'t-14 t-normal')]/span|.//span[contains(@class,'t-14 t-normal')]")
            if degree_field:
                # Heuristic: degree | field separated by "·" or "-"
                df_text = [get_text(x) for x in degree_field if get_text(x)]
                if df_text:
                    # Try to split degree/field if pattern present
                    parts = df_text[0].split("·")
                    if len(parts) >= 1: edu.degree = parts[0].strip()
                    if len(parts) >= 2: edu.field = parts[1].strip()

            date_range = item.find_elements(By.XPATH, ".//span[contains(@class,'t-14 t-normal t-black--light')]/span|.//span[contains(@class,'t-14 t-normal t-black--light')]")
            if date_range:
                edu.date_range = get_text(date_range[0])

            desc = item.find_elements(By.XPATH, ".//div[contains(@class,'inline-show-more-text') or contains(@class,'show-more-less-text')]")
            if desc:
                edu.description = get_text(desc[0])

            if any([edu.school, edu.degree, edu.field, edu.date_range, edu.description]):
                data.education.append(edu)
        except Exception:
            continue

def extract_skills(driver: webdriver.Chrome, data: ProfileData):
    sec = find_section_by_heading(driver, "Skills")
    data.skills = []
    if not sec:
        return

    scroll_to_element(driver, sec)
    expand_all_see_more_in_section(sec, driver)

    # Skill chips often as <span> inside list items
    chips = sec.find_elements(By.XPATH, ".//span[contains(@class,'mr1')]/span|.//a//span[contains(@class,'mr1')]/span|.//span[contains(@class,'t-bold')]/span")
    for chip in chips:
        txt = get_text(chip)
        if txt and txt.lower() not in [s.lower() for s in data.skills]:
            data.skills.append(txt)

def open_contact_info(driver: webdriver.Chrome):
    """
    Try to open contact info modal (if available).
    """
    # Typically a button with 'Contact info' text near header
    clicked = click_if_present(
        driver,
        By.XPATH,
        "//a[contains(@href,'contact-info')] | //a[.//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'contact info')]]",
        timeout=2
    )
    if not clicked:
        return None
    # Wait for modal
    modal = safe_find(driver, By.XPATH, "//div[@role='dialog' or @role='alertdialog']", timeout=5)
    return modal

def extract_contact_info(driver: webdriver.Chrome, data: ProfileData):
    data.websites = []
    modal = open_contact_info(driver)
    if not modal:
        return

    # Websites
    links = modal.find_elements(By.XPATH, ".//a[@href and not(contains(@href,'mailto:'))]")
    for a in links:
        href = a.get_attribute("href")
        if href and "linkedin.com" not in href:
            data.websites.append(href)

    # Email
    mailto = modal.find_elements(By.XPATH, ".//a[starts-with(@href,'mailto:')]")
    if mailto:
        data.email = mailto[0].get_attribute("href").replace("mailto:", "").strip()

    # Close modal (Esc)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    randsleep(0.2, 0.4)

# ------------------------------ Core ------------------------------------

def linkedin_login(driver):
    load_dotenv()
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASS")
    if not email or not password:
        raise RuntimeError("Missing LINKEDIN_EMAIL or LINKEDIN_PASS in .env")

    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.ID, "username")))

    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, '//button[@type="submit"]').click()

    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.url_contains("feed"))
    print("✅ Logged in")

def scrape_profile(driver, url: str) -> Dict:
    data = ProfileData(url=url)

    # Clean & go
    clean_url = url.split("?")[0]
    if not clean_url.endswith("/"):
        clean_url += "/"
    driver.get(clean_url)
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    randsleep(1.2, 2.0)

    # Basic auth walls
    if "checkpoint" in driver.current_url or "login" in driver.current_url:
        raise RuntimeError("Not authenticated or hit a checkpoint wall.")

    # Gentle progressive scroll to load lazy sections
    scroll_page(driver, steps=8)

    # Extract
    extract_header(driver, data)
    extract_about(driver, data)
    extract_experience(driver, data)
    extract_education(driver, data)
    extract_skills(driver, data)
    extract_contact_info(driver, data)

    # Return as dict
    return asdict(data)

def make_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()

    # (Optional) headless; note: visible browsers sometimes fare better with anti-bot systems
    if headless:
        opts.add_argument("--headless=new")

    # Stability / best practices
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--lang=en-US")

    # A modest, realistic UA string
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_page_load_timeout(45)
    return driver

# ------------------------------ Entrypoint -------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_linkedin_profile.py <linkedin_profile_url>")
        sys.exit(1)

    url = sys.argv[1].strip()
    driver = make_driver(headless=False)  # set True if you must run headless
    try:
        linkedin_login(driver)
        result = scrape_profile(driver, url)
        
        # Print to stdout for subprocess capture
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output)
        
        # Also save to fileeee
        if result.get('name'):
            # Use name for filename, fallback to timestamp
            filename = f"{result['name'].replace(' ', '_').lower()}_linkedin.json"
        else:
            filename = f"linkedin_profile_{int(time.time())}.json"
        
        os.makedirs("scraped_data", exist_ok=True)
        filepath = os.path.join("scraped_data", filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_output)
        
        print(f"Data saved to: {filepath}", file=sys.stderr)
        
    finally:
        # Small human-like pause before closing
        randsleep(0.5, 1.2)
        driver.quit()

if __name__ == "__main__":
    main()
