"""Page Object: AccountPage - Phụ trách: TV1 (Trung) - Module: ACC, HIS.
Quy tắc Page Object Model (POM):
1. Khai báo Locators dạng tuple (By.<TYPE>, "selector") ở đầu lớp.
2. Các methods là các hành vi nghiệp vụ thực tế của người dùng.
3. TUYỆT ĐỐI KHÔNG đặt lệnh assert trong Page Object (chỉ assert trong file tests/).
4. Tự động xử lý và cách ly các cửa sổ nổi/popup tránh gây fail sai lệch.
"""
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from pages.base_page import BasePage


class AccountPage(BasePage):
    PATH = "/account/info"

    # ---- Locators điều hướng trang tài khoản Coolmate
    PROFILE_TAB = (By.XPATH, "//a[contains(@href, '/account/info')]")
    ORDERS_TAB = (By.XPATH, "//a[contains(@href, '/account/orders') or contains(., 'Lịch sử')]")
    LOGOUT_BTN = (By.XPATH, "//a[contains(@href, 'logout')] | //button[contains(., 'Đăng xuất')]")

    # ---- Nút mở modal chỉnh sửa thông tin cá nhân (nút 'Cập nhật' đầu tiên)
    OPEN_EDIT_BTN = (By.XPATH, "(//button[contains(normalize-space(.), 'Cập nhật') or contains(normalize-space(.), 'CẬP NHẬT')])[1]")

    # ---- Locators bên trong modal chỉnh sửa thông tin cá nhân (được cô lập hoàn toàn)
    EDIT_MODAL = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='fullname']]")
    NAME_INPUT = (By.NAME, "fullname")
    PHONE_INPUT = (By.NAME, "phone")
    SAVE_BTN = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='fullname']]//button[contains(normalize-space(.), 'Cập nhật thông tin') or contains(normalize-space(.), 'CẬP NHẬT THÔNG TIN')]")
    CLOSE_MODAL_BTN = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='fullname']]//button[contains(., 'Close') or contains(@class, 'right-1') or contains(@class, 'close')]")
    ERROR_MESSAGE = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='fullname']]//*[contains(text(), 'không hợp lệ') or contains(text(), 'Vui lòng') or contains(text(), 'bắt buộc')]")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".toast-success, .alert-success, .success-message, [data-type='success']")

    # ---- Locators đổi mật khẩu (nút 'Cập nhật' thứ hai)
    OPEN_PASSWORD_MODAL_BTN = (By.XPATH, "(//button[contains(normalize-space(.), 'Cập nhật') or contains(normalize-space(.), 'CẬP NHẬT')])[2]")
    PASSWORD_MODAL = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='old_password']]")
    OLD_PASSWORD_INPUT = (By.NAME, "old_password")
    NEW_PASSWORD_INPUT = (By.NAME, "password")
    CONFIRM_PASSWORD_INPUT = (By.NAME, "password_confirmation")
    SAVE_PASSWORD_BTN = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='old_password']]//button[contains(., 'Cập nhật') or contains(., 'CẬP NHẬT')]")
    CLOSE_PASSWORD_MODAL_BTN = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='old_password']]//button[contains(., 'Close') or contains(@class, 'right-1')]")
    PASSWORD_ERROR_MESSAGE = (By.XPATH, "//div[contains(., 'Chỉnh sửa thông tin') and .//input[@name='old_password']]//*[contains(text(), 'không đúng') or contains(text(), 'không khớp') or contains(text(), 'Vui lòng') or contains(text(), 'tối thiểu')]")

    def load(self):
        """Mở trực tiếp trang tài khoản và loại bỏ mọi popup quảng cáo xuất hiện."""
        self.open(self.PATH)
        time.sleep(2)
        self.dismiss_popups()
        return self

    def is_at_account_page(self):
        """Kiểm tra người dùng có đang ở trang thông tin tài khoản hay không."""
        return "/account" in self.driver.current_url.lower()

    def get_name_value(self):
        """Lấy họ tên hiển thị trên trang tài khoản."""
        self.dismiss_popups()
        try:
            inp = self.driver.find_element(*self.NAME_INPUT)
            if inp.is_displayed():
                val = inp.get_attribute("value")
                if val:
                    return val.strip()
        except Exception:
            pass
        try:
            elems = self.driver.find_elements(By.XPATH, "//*[text()='Họ và tên']/following-sibling::* | //*[text()='Họ và tên']/../*")
            for el in elems:
                t = el.text.strip()
                if t and t != "Họ và tên" and "CẬP NHẬT" not in t.upper():
                    return t
        except Exception:
            pass
        try:
            headings = self.driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4")
            for h in headings:
                t = h.text.strip()
                if t.startswith("Chào ") or t.startswith("Hi "):
                    name = t.replace("Chào ", "").replace("Hi ", "").split(",")[0].strip()
                    if name:
                        return name
        except Exception:
            pass
        return ""

    def get_phone_value(self):
        """Lấy số điện thoại hiển thị trên trang tài khoản."""
        self.dismiss_popups()
        try:
            inp = self.driver.find_element(*self.PHONE_INPUT)
            if inp.is_displayed():
                val = inp.get_attribute("value")
                if val:
                    return val.strip()
        except Exception:
            pass
        try:
            elems = self.driver.find_elements(By.XPATH, "//*[text()='Số điện thoại']/following-sibling::* | //*[text()='Số điện thoại']/../*")
            for el in elems:
                t = el.text.strip()
                if t and t != "Số điện thoại" and any(c.isdigit() for c in t) and "CẬP NHẬT" not in t.upper():
                    return t
        except Exception:
            pass
        return ""

    def open_edit_modal(self):
        """Bấm nút CẬP NHẬT để mở modal chỉnh sửa thông tin."""
        self.dismiss_popups()
        if self.is_visible(self.NAME_INPUT, timeout=1):
            return self
        try:
            btns = [b for b in self.driver.find_elements(*self.OPEN_EDIT_BTN) if b.is_displayed()]
            if btns:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btns[0])
                self.driver.execute_script("arguments[0].click();", btns[0])
                time.sleep(1.5)
        except Exception:
            pass
        return self

    def close_edit_modal(self):
        """Đóng modal chỉnh sửa để đưa giao diện về trạng thái ban đầu."""
        try:
            close_btns = self.driver.find_elements(*self.CLOSE_MODAL_BTN)
            for b in close_btns:
                if b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1)
                    return self
        except Exception:
            pass
        return self

    def update_name(self, new_name):
        """Cập nhật họ tên mới qua modal."""
        self.open_edit_modal()
        self.type(self.NAME_INPUT, new_name, clear=True)
        time.sleep(0.5)
        btn = self.driver.find_element(*self.SAVE_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2.0)
        return self

    def update_phone(self, new_phone):
        """Cập nhật số điện thoại mới qua modal."""
        self.open_edit_modal()
        self.type(self.PHONE_INPUT, new_phone, clear=True)
        time.sleep(0.5)
        btn = self.driver.find_element(*self.SAVE_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        return self

    def update_profile_valid(self, fullname, phone, gender="male"):
        """Cập nhật thông tin cá nhân đầy đủ (ACC-03)."""
        self.open_edit_modal()
        self.type(self.NAME_INPUT, fullname, clear=True)
        self.type(self.PHONE_INPUT, phone, clear=True)
        time.sleep(0.3)
        # Chọn giới tính nếu có
        try:
            radio = self.driver.find_element(By.CSS_SELECTOR, f"input[value='{gender}']")
            self.driver.execute_script("arguments[0].click();", radio)
        except Exception:
            pass
        time.sleep(0.3)
        btn = self.driver.find_element(*self.SAVE_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(2.0)
        return self

    def clear_name_and_save(self):
        """Xóa trắng ô họ tên rồi bấm lưu trong modal (ACC-05)."""
        self.open_edit_modal()
        self.type(self.NAME_INPUT, "", clear=True)
        time.sleep(0.5)
        btn = self.driver.find_element(*self.SAVE_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        return self

    def get_error_message(self):
        """Lấy nội dung thông báo lỗi bên trong modal."""
        try:
            elems = self.driver.find_elements(*self.ERROR_MESSAGE)
            for el in elems:
                if el.is_displayed() and el.text.strip():
                    return el.text.strip()
        except Exception:
            pass
        return ""

    # ---- Các hành động Đổi Mật Khẩu (ACC-07, ACC-08, ACC-09)
    def open_password_modal(self):
        """Mở modal đổi mật khẩu."""
        self.dismiss_popups()
        if self.is_visible(self.OLD_PASSWORD_INPUT, timeout=1):
            return self
        try:
            btn = self.driver.find_element(*self.OPEN_PASSWORD_MODAL_BTN)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5)
        except Exception:
            pass
        return self

    def close_password_modal(self):
        """Đóng modal đổi mật khẩu."""
        try:
            close_btns = self.driver.find_elements(*self.CLOSE_PASSWORD_MODAL_BTN)
            for b in close_btns:
                if b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1)
                    return self
        except Exception:
            pass
        return self

    def submit_password_change(self, old_pass, new_pass, confirm_pass):
        """Điền thông tin và bấm Cập nhật mật khẩu."""
        self.open_password_modal()
        self.type(self.OLD_PASSWORD_INPUT, old_pass, clear=True)
        self.type(self.NEW_PASSWORD_INPUT, new_pass, clear=True)
        self.type(self.CONFIRM_PASSWORD_INPUT, confirm_pass, clear=True)
        time.sleep(0.5)
        btn = self.driver.find_element(*self.SAVE_PASSWORD_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(1.5)
        return self

    def get_password_error_message(self):
        """Lấy thông báo lỗi trong modal đổi mật khẩu."""
        try:
            elems = self.driver.find_elements(*self.PASSWORD_ERROR_MESSAGE)
            for el in elems:
                if el.is_displayed() and el.text.strip():
                    return el.text.strip()
        except Exception:
            pass
        return ""
