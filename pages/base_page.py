"""Lớp cha của mọi Page Object: chỉ chứa thao tác dùng chung. Chỉ TV1 sửa file này."""
from datetime import datetime
from pathlib import Path

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import config

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "evidence"


class BasePage:
    # Locator popup quảng cáo/cookie: điền sau khi khảo sát site thật
    POPUP_CLOSE_LOCATORS = []  # ví dụ: [(By.CSS_SELECTOR, "button.close")]

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)

    # ---- điều hướng
    def open(self, path=""):
        self.driver.get(config.BASE_URL.rstrip("/") + path)
        self.dismiss_popups()
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
        if clear:
            el.clear()
        el.send_keys(text)

    def text_of(self, locator):
        return self.visible(locator).text.strip()

    def scroll_to(self, locator):
        el = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        return el

    def dismiss_popups(self):
        for locator in self.POPUP_CLOSE_LOCATORS:
            if self.is_visible(locator, timeout=1):
                self.click(locator)

    # ---- bằng chứng
    def take_screenshot(self, name, sub="manual"):
        folder = EVIDENCE_DIR / sub
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}_{datetime.now():%Y%m%d}.png"
        self.driver.save_screenshot(str(path))
        return path
