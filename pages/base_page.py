"""Lớp cha của mọi Page Object: chỉ chứa thao tác dùng chung. Phụ trách: TV1 (Trung)."""
from datetime import datetime
from pathlib import Path
import time

from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils import config

EVIDENCE_DIR = Path(__file__).resolve().parent.parent / "evidence"


class BasePage:
    # Danh sách bộ chọn popup quảng cáo, cookie, modal chào mừng Coolmate
    POPUP_CLOSE_LOCATORS = [
        (By.XPATH, "//button[contains(normalize-space(.), 'Chấp nhận tất cả') or contains(normalize-space(.), 'Chấp nhận')]"),
        (By.XPATH, "//button[contains(@class, 'absolute') and (contains(., 'Close') or contains(@class, 'right-1') or contains(@class, 'rounded-full'))]"),
        (By.XPATH, "//button[contains(normalize-space(.), 'Bỏ qua bước này') or contains(normalize-space(.), 'Bỏ qua')]"),
        (By.CSS_SELECTOR, "button[aria-label='Close'], button[aria-label='Đóng']"),
        (By.XPATH, "//button[normalize-space(.)='×' or normalize-space(.)='X']"),
    ]

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)

    # ---- điều hướng
    def open(self, path=""):
        self.driver.get(config.BASE_URL.rstrip("/") + path)
        self.dismiss_popups()
        return self

    # ---- chờ tường minh (không dùng time.sleep cố định)
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
        except (TimeoutException, StaleElementReferenceException):
            return False

    # ---- thao tác
    def click(self, locator):
        """Click vào phần tử, nếu bị che bởi overlay/popup thì dùng JavaScript click dự phòng."""
        el = self.clickable(locator)
        try:
            el.click()
        except (ElementClickInterceptedException, Exception):
            self.dismiss_popups()
            self.driver.execute_script("arguments[0].click();", el)

    def type(self, locator, text, clear=True):
        """Nhập dữ liệu tương thích hoàn hảo với React state (sử dụng HTMLInputElement native prototype setter)."""
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
        """Tự động đóng tất cả các loại popup nổi (cookie, Cool Club, khuyến mãi) mà không làm gián đoạn test."""
        close_xpaths = [
            "//button[contains(normalize-space(.), 'Chấp nhận tất cả') or contains(normalize-space(.), 'Chấp nhận')]",
            "//button[contains(@class, 'absolute') and (contains(., 'Close') or contains(@class, 'right-1') or contains(@class, 'rounded-full'))]",
            "//button[contains(normalize-space(.), 'Bỏ qua bước này') or contains(normalize-space(.), 'Bỏ qua')]",
            "//button[@aria-label='Close' or @aria-label='Đóng' or normalize-space(.)='×' or normalize-space(.)='X']"
        ]
        for xp in close_xpaths:
            try:
                elements = self.driver.find_elements(By.XPATH, xp)
                for el in elements:
                    try:
                        if el.is_displayed():
                            self.driver.execute_script("arguments[0].click();", el)
                            time.sleep(0.5)
                            break
                    except Exception:
                        pass
            except Exception:
                pass

    def take_screenshot(self, name, sub="manual"):
        """Theo yêu cầu: không xuất ảnh chụp màn hình, chỉ lưu trữ vết log."""
        pass
