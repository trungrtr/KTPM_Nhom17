"""Page Object: RegisterPage - Module REG.

Chứa các thao tác đăng ký tài khoản Coolmate.
Không sử dụng assert trong Page Object.
"""

import sys
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pages.base_page import BasePage


def _print(*args, **kwargs):
    """print() an toàn trên Windows (tránh UnicodeEncodeError với cp1252)."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"), **kwargs)


class RegisterPage(BasePage):

    PATH = "/register"

    # ========== LOCATORS ==========

    COOKIE_ACCEPT_BTN = (
        By.XPATH,
        "//button[contains(normalize-space(.), 'Chấp nhận tất cả')]"
    )

    REGISTER_LINK = (
        By.XPATH,
        "//*[self::button or self::a]"
        "[contains(normalize-space(.), 'Đăng ký tài khoản mới')]"
    )

    NAME_INPUT = (
        By.CSS_SELECTOR,
        "input[name='fullname']"
    )

    PHONE_INPUT = (
        By.CSS_SELECTOR,
        "input[name='phone']"
    )

    EMAIL_INPUT = (
        By.CSS_SELECTOR,
        "input[name='email']"
    )

    PASSWORD_INPUT = (
        By.CSS_SELECTOR,
        "input[name='password']"
    )

    SUBMIT_BTN = (
        By.CSS_SELECTOR,
        "button[ga-tracking-value='register_account']"
    )

    PASSWORD_TOGGLE = (
        By.CSS_SELECTOR,
        "button[class*='password'], "
        ".toggle-password, "
        "[data-action='toggle-password'], "
        "[aria-label*='mật khẩu']"
    )

    LOGIN_LINK = (
        By.CSS_SELECTOR,
        "a[href*='login'], a[href*='dang-nhap']"
    )

    ERROR_MESSAGE = (
        By.CSS_SELECTOR,
        ".error-message, .form-error, .text-red-500, "
        ".text-danger, [class*='error'], [role='alert']"
    )

    SUCCESS_MESSAGE = (
        By.CSS_SELECTOR,
        ".success-message, .alert-success, [class*='success']"
    )

    # ========== XỬ LÝ COOKIE ==========

    def accept_cookies(self):
        """Chấp nhận Cookie nếu hiển thị."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    self.COOKIE_ACCEPT_BTN
                )
            ).click()
            _print("[REG] Đã chấp nhận cookie")
        except TimeoutException:
            _print("[REG] Không có thông báo cookie")

    # ========== MỞ FORM ĐĂNG KÝ ==========

    def load(self):
        """Mở trực tiếp trang đăng ký Coolmate."""
        self.open(self.PATH)

        # Xử lý cookie
        self.accept_cookies()

        wait = WebDriverWait(self.driver, 15)

        # Chờ form đăng ký hiển thị
        wait.until(EC.visibility_of_element_located(self.NAME_INPUT))
        wait.until(EC.visibility_of_element_located(self.PHONE_INPUT))
        wait.until(EC.visibility_of_element_located(self.EMAIL_INPUT))
        wait.until(EC.visibility_of_element_located(self.PASSWORD_INPUT))
        wait.until(EC.visibility_of_element_located(self.SUBMIT_BTN))

        _print("[REG] Đã mở đúng form đăng ký")
        _print("[REG] URL:", self.driver.current_url)
        return self

    # ========== NHẬP THÔNG TIN ==========

    def fill_name(self, name):
        self.type(self.NAME_INPUT, name)

    def fill_phone(self, phone):
        self.type(self.PHONE_INPUT, phone)

    def fill_email(self, email):
        self.type(self.EMAIL_INPUT, email)

    def fill_password(self, password):
        self.type(self.PASSWORD_INPUT, password)

    # ========== BẤM ĐĂNG KÝ ==========

    def click_register(self):
        """Bấm đúng nút đăng ký."""
        button = self.visible(self.SUBMIT_BTN)

        _print("[REG] Nút:", button.text)
        _print("[REG] Enabled:", button.is_enabled())

        if not button.is_enabled():
            _print("[REG] Nút đăng ký bị vô hiệu hóa")
            return False

        button.click()
        _print("[REG] Đã bấm nút đăng ký")
        return True

    def register(self, name="", email="", phone="", password=""):
        """Điền thông tin rồi bấm đăng ký."""
        if name:
            self.fill_name(name)
        if email:
            self.fill_email(email)
        if phone:
            self.fill_phone(phone)
        if password:
            self.fill_password(password)
        return self.click_register()

    # ========== LINK ĐĂNG NHẬP ==========

    def click_login_link(self):
        self.click(self.LOGIN_LINK)

    # ========== HIỂN THỊ MẬT KHẨU ==========

    def click_password_toggle(self):
        self.click(self.PASSWORD_TOGGLE)

    def get_password_field_type(self):
        return self.find(self.PASSWORD_INPUT).get_attribute("type")

    # ========== KIỂM TRA TRẠNG THÁI ==========

    def is_on_register_page(self):
        """Kiểm tra form đăng ký đang hiển thị."""
        if "/register" not in self.driver.current_url.lower():
            return False

        name_elements = self.driver.find_elements(*self.NAME_INPUT)
        submit_elements = self.driver.find_elements(*self.SUBMIT_BTN)

        return (
            any(el.is_displayed() for el in name_elements)
            and
            any(el.is_displayed() for el in submit_elements)
        )

    def has_error(self):
        return bool(self.get_all_errors())

    def get_error_message(self):
        errors = self.get_all_errors()
        return errors[0] if errors else ""

    def get_all_errors(self):
        """Lấy thông báo lỗi đang hiển thị."""
        elements = self.driver.find_elements(*self.ERROR_MESSAGE)
        return [
            el.text.strip()
            for el in elements
            if el.is_displayed() and el.text.strip()
        ]

    def is_registered_successfully(self):
        """Kiểm tra thông báo đăng ký thành công."""
        return self.is_visible(self.SUCCESS_MESSAGE, timeout=10)

    # ========== HELPER ==========

    @staticmethod
    def generate_email(prefix="reg"):
        ts = time.time_ns()
        return f"nhom17.test+{prefix}{ts}@gmail.com"
