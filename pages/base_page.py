"""Lớp cha của mọi Page Object: chỉ chứa thao tác dùng chung. Chỉ TV1 sửa file này."""
from datetime import datetime
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import config

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "evidence"


class BasePage:
    # Locator popup quảng cáo, cookie, modal chào mừng Coolmate
    POPUP_CLOSE_LOCATORS = [
        (By.XPATH, "//button[contains(., 'Chấp nhận tất cả')]"),
        (By.XPATH, "//button[contains(@class, 'rounded-full') and (contains(., 'Close') or contains(@class, 'bg-neutral-900'))]"),
        (By.CSS_SELECTOR, "button[aria-label='Close']"),
    ]

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)

    # ---- điều hướng
    def open(self, path=""):
        self.driver.get(config.BASE_URL.rstrip("/") + path)
        return self

    # ---- chờ tường minh (không dùng time.sleep)
    def find(self, locator):
        return self.wait.until(EC.presence_of_element_located(locator))

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def is_visible(self, locator, timeout=3):
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    # ---- thao tác
    def click(self, locator):
        self.clickable(locator).click()

    def type(self, locator, text, clear=True):
        el = self.visible(locator)
        self.scroll_to(locator)
        js_setter = """
        const input = arguments[0];
        const value = arguments[1];
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        if (nativeSetter) {
            nativeSetter.call(input, value);
        } else {
            input.value = value;
        }
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        """
        try:
            self.driver.execute_script(js_setter, el, text)
        except Exception:
            if clear:
                try:
                    el.clear()
                except Exception:
                    pass
            el.send_keys(text)

    def text_of(self, locator):
        return self.visible(locator).text.strip()

    def scroll_to(self, locator):
        el = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def dismiss_popups(self):
        import time
        close_selectors = [
            "//button[contains(@class, 'absolute') and contains(@class, 'rounded-full') and (contains(., 'Close') or contains(@class, 'right-'))]",
            "//button[text()='Close']",
            "//button[contains(., 'Chấp nhận tất cả')]"
        ]
        for sel in close_selectors:
            try:
                for b in self.driver.find_elements(By.XPATH, sel):
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(0.3)
            except Exception:
                pass

    # ---- bằng chứng
    def take_screenshot(self, name, sub="manual"):
        folder = EVIDENCE_DIR / sub
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}_{datetime.now():%Y%m%d}.png"
        self.driver.save_screenshot(str(path))
        return path
