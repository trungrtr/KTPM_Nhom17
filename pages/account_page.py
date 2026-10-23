"""Page Object: AccountPage - phụ trách: TV1 (Trung) - module: ACC, HIS.
Quy tắc:
1. Locator đặt ở đầu lớp dạng Tuple (By.<TYPE>, "selector").
2. Methods là các hành động nghiệp vụ thực tế của người dùng.
3. KHÔNG đặt lệnh assert trong Page Object.
"""
import time
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class AccountPage(BasePage):
    PATH = "/account/info"

    # ---- Locators giao diện trang thông tin tài khoản Coolmate
    PROFILE_TAB = (By.XPATH, "//a[contains(@href, '/account/info')]")
    
    # Nút mở modal chỉnh sửa thông tin (nút 'Cập nhật' ở khối thông tin)
    OPEN_EDIT_BTN = (By.XPATH, "//button[text()='Cập nhật']")
    
    # Locators trong form chỉnh sửa
    NAME_INPUT = (By.NAME, "fullname")
    PHONE_INPUT = (By.NAME, "phone")
    SAVE_BTN = (By.XPATH, "//button[contains(text(), 'Cập nhật thông tin')]")
    CLOSE_MODAL_BTN = (By.XPATH, "//button[contains(@class, 'absolute') and (contains(., 'Close') or contains(@class, 'right-'))]")
    
    # Thông báo lỗi trong modal (chứa từ khóa lỗi)
    ERROR_MESSAGE = (By.XPATH, "//div[contains(@role, 'dialog') or .//input[@name='fullname']]//*[contains(text(), 'không hợp lệ') or contains(text(), 'Vui lòng') or contains(text(), 'bắt buộc')]")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".toast-success, .alert-success, .success-message, [data-type='success']")
    
    # Nút đăng xuất
    LOGOUT_BTN = (By.XPATH, "//a[contains(@href, 'logout')] | //button[contains(., 'Đăng xuất')]")

    def load(self):
        """Mở trực tiếp trang tài khoản và đóng popups nếu có."""
        self.open(self.PATH)
        time.sleep(3)
        self.dismiss_popups()
        return self

    def is_at_account_page(self):
        """Kiểm tra có đang ở trang thông tin tài khoản hay không."""
        return "/account" in self.driver.current_url.lower()

    def get_name_value(self):
        """Lấy họ tên hiển thị trên trang tài khoản."""
        # 1. Nếu đang mở modal input
        try:
            inp = self.driver.find_element(*self.NAME_INPUT)
            if inp.is_displayed():
                val = inp.get_attribute("value")
                if val:
                    return val
        except Exception:
            pass
        # 2. Tìm trong khối text thông tin tài khoản
        try:
            elems = self.driver.find_elements(By.XPATH, "//*[text()='Họ và tên']/following-sibling::* | //*[text()='Họ và tên']/../*")
            for el in elems:
                t = el.text.strip()
                if t and t != "Họ và tên":
                    return t
        except Exception:
            pass
        try:
            elems = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Đào Quang Trung')]")
            if elems:
                return elems[0].text.strip()
        except Exception:
            pass
        return ""

    def get_phone_value(self):
        """Lấy số điện thoại hiển thị trên trang tài khoản."""
        try:
            inp = self.driver.find_element(*self.PHONE_INPUT)
            if inp.is_displayed():
                val = inp.get_attribute("value")
                if val:
                    return val
        except Exception:
            pass
        try:
            elems = self.driver.find_elements(By.XPATH, "//*[text()='Số điện thoại']/following-sibling::* | //*[text()='Số điện thoại']/../*")
            for el in elems:
                t = el.text.strip()
                if t and t != "Số điện thoại" and any(c.isdigit() for c in t):
                    return t
        except Exception:
            pass
        return ""

    def open_edit_modal(self):
        """Bấm nút CẬP NHẬT để mở modal chỉnh sửa thông tin nếu chưa mở."""
        self.dismiss_popups()
        if self.is_visible(self.NAME_INPUT, timeout=1):
            return self
        try:
            btns = self.driver.find_elements(*self.OPEN_EDIT_BTN)
            for b in btns:
                if b.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1.5)
                    break
        except Exception:
            pass
        return self

    def close_edit_modal(self):
        """Đóng modal chỉnh sửa để quay lại giao diện ban đầu."""
        try:
            for b in self.driver.find_elements(*self.CLOSE_MODAL_BTN):
                if b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1)
                    break
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
        time.sleep(2.5)
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
        """Lấy nội dung thông báo lỗi nếu có."""
        try:
            elems = self.driver.find_elements(*self.ERROR_MESSAGE)
            for el in elems:
                if el.is_displayed() and el.text.strip():
                    return el.text.strip()
        except Exception:
            pass
        return ""

    def get_success_message(self):
        """Lấy nội dung thông báo thành công nếu có."""
        if self.is_visible(self.SUCCESS_MESSAGE, timeout=3):
            return self.text_of(self.SUCCESS_MESSAGE)
        return ""
