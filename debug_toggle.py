"""Debug: khao sat nut an/hien mat khau."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://www.coolmate.me/register")
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Chấp nhận tất cả')]"))
        ).click()
    except TimeoutException:
        pass

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
    )

    # Find the password input and its surrounding HTML
    pw_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
    parent = pw_input.find_element(By.XPATH, "./..")
    grandparent = parent.find_element(By.XPATH, "./..")

    print("=== PASSWORD INPUT ===")
    print(f"Tag: {pw_input.tag_name}")
    print(f"Type: {pw_input.get_attribute('type')}")

    print("\n=== PARENT ===")
    print(f"Tag: {parent.tag_name}")
    print(f"Class: {parent.get_attribute('class')}")
    print(f"Inner HTML (first 500):\n{parent.get_attribute('innerHTML')[:500]}")

    print("\n=== GRANDPARENT ===")
    print(f"Tag: {grandparent.tag_name}")
    print(f"Class: {grandparent.get_attribute('class')}")
    print(f"Inner HTML (first 1000):\n{grandparent.get_attribute('innerHTML')[:1000]}")

    # Look for any toggle-like elements near password
    selectors_to_try = [
        "button[class*='password']",
        ".toggle-password",
        "[data-action='toggle-password']",
        "[aria-label*='mật khẩu']",
        "button[class*='eye']",
        "[class*='eye']",
        "[class*='toggle']",
        "svg",
        "button[type='button']",
    ]

    print("\n=== LOOKING FOR TOGGLE ELEMENTS ===")
    for sel in selectors_to_try:
        try:
            els = grandparent.find_elements(By.CSS_SELECTOR, sel)
            if els:
                for e in els:
                    print(f"  {sel}: tag={e.tag_name} class={e.get_attribute('class')!r} visible={e.is_displayed()} text={e.text[:50]!r}")
        except:
            pass

    # Also search globally
    print("\n=== GLOBAL SEARCH FOR EYE/TOGGLE BUTTONS ===")
    for sel in ["[class*='eye']", "[class*='toggle']", "[class*='show']", "[class*='hide']",
                "button[class*='password']", "[aria-label*='password']", "[aria-label*='show']"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        for e in els:
            if e.is_displayed():
                print(f"  {sel}: tag={e.tag_name} class={e.get_attribute('class')!r} text={e.text[:50]!r}")

finally:
    driver.quit()
