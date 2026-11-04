"""Debug: khao sat form dang ky Coolmate thuc te."""
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
import time

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get("https://www.coolmate.me/register")
    print(f"URL: {driver.current_url}")
    print(f"Title: {driver.title}")
    time.sleep(3)

    # Try to accept cookies
    try:
        cookie_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Chấp nhận tất cả')]"))
        )
        cookie_btn.click()
        print("Cookie accepted")
        time.sleep(2)
    except TimeoutException:
        print("No cookie popup")

    print(f"Final URL: {driver.current_url}")
    print(f"Page source length: {len(driver.page_source)}")

    # List all input elements
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\n=== ALL INPUT ELEMENTS ({len(inputs)}) ===")
    for i, inp in enumerate(inputs):
        name = inp.get_attribute("name") or ""
        type_ = inp.get_attribute("type") or ""
        ph = inp.get_attribute("placeholder") or ""
        vis = inp.is_displayed()
        print(f"  [{i}] name={name!r} type={type_!r} placeholder={ph!r} visible={vis}")

    # List all buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"\n=== ALL BUTTON ELEMENTS ({len(buttons)}) ===")
    for i, btn in enumerate(buttons):
        text = btn.text.strip()[:80]
        vis = btn.is_displayed()
        ga = btn.get_attribute("ga-tracking-value") or ""
        cls = btn.get_attribute("class") or ""
        print(f"  [{i}] text={text!r} visible={vis} ga={ga!r} class={cls[:60]!r}")

    # Check specific selectors
    selectors = [
        "input[name='fullName']",
        "input[name='phone']",
        "input[name='email']",
        "input[name='password']",
        "button[ga-tracking-value='register_account']",
        "input[name='full_name']",
        "input[name='name']",
        "input[placeholder*='tên']",
        "input[placeholder*='Tên']",
        "input[placeholder*='ten']",
        "form",
    ]
    print("\n=== SELECTOR CHECK ===")
    for sel in selectors:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        count = len(els)
        vis = sum(1 for e in els if e.is_displayed())
        print(f"  {sel}: found={count} visible={vis}")

    # Save screenshot
    driver.save_screenshot("results/reg_debug.png")
    print("\nScreenshot saved to results/reg_debug.png")

finally:
    driver.quit()
