"""Page Object: CheckoutPage - Phụ trách: TV1 (Trung) / TV4 (Huy) - Module: ORD.
Kiến trúc POM:
1. Locators đặt ở đầu lớp dạng tuple.
2. Methods là các hành động nghiệp vụ thực tế (chọn COD, điền thông tin, dừng trước xác nhận).
3. KHÔNG đặt assert trong Page Object.
4. Tự động xử lý popup và tương thích với React input.
"""
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    PATH = "/cart"

    # ---- Locators giỏ hàng & thanh toán Coolmate
    EMPTY_CART_MESSAGE = (By.XPATH, "//*[contains(text(), 'Giỏ hàng của bạn trống')]")
    CHECKOUT_SECTION = (By.XPATH, "//*[contains(., 'Thông tin giao hàng') or .//input[@name='fullname']]")

    # ---- Các trường thông tin nhận hàng
    FULLNAME_INPUT = (By.CSS_SELECTOR, "input[name='fullname'], input[placeholder*='họ tên']")
    PHONE_INPUT = (By.CSS_SELECTOR, "input[name='phone'], input[placeholder*='số điện thoại']")
    EMAIL_INPUT = (By.CSS_SELECTOR, "input[name='email'], input[placeholder*='email']")
    ADDRESS_INPUT = (By.CSS_SELECTOR, "input[placeholder*='địa chỉ']")
    PROVINCE_INPUT = (By.CSS_SELECTOR, "input[placeholder*='tỉnh/thành phố']")
    DISTRICT_INPUT = (By.CSS_SELECTOR, "input[placeholder*='quận/huyện']")
    WARD_INPUT = (By.CSS_SELECTOR, "input[placeholder*='phường/xã']")

    # ---- Phương thức thanh toán
    COD_PAYMENT_OPTION = (By.XPATH, "//*[contains(text(), 'Thanh toán khi nhận hàng') or contains(text(), 'COD')]")
    ONLINE_PAYMENT_OPTION = (By.XPATH, "//*[contains(text(), 'VNPAY') or contains(text(), 'Ví MoMo') or contains(text(), 'thẻ')]")

    # ---- Nút đặt hàng & voucher
    ORDER_SUBMIT_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'ĐẶT HÀNG') or contains(normalize-space(.), 'Đặt hàng')]")
    VOUCHER_INPUT = (By.NAME, "voucher")
    APPLY_VOUCHER_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'ÁP DỤNG') or contains(normalize-space(.), 'Áp dụng')]")

    # ---- Báo lỗi validation
    FIELD_ERRORS = (By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'text-red') or contains(text(), 'Vui lòng') or contains(text(), 'bắt buộc') or contains(text(), 'không hợp lệ')]")

    def load(self):
        """Mở trang thanh toán/giỏ hàng và dọn sạch popup."""
        self.open(self.PATH)
        time.sleep(2)
        self.dismiss_popups()
        return self

    def is_empty_cart(self):
        """Kiểm tra giỏ hàng có đang trống hay không."""
        return self.is_visible(self.EMPTY_CART_MESSAGE, timeout=2) or "trống" in self.driver.page_source.lower()

    def add_sample_product_to_cart(self, product_url="https://www.coolmate.me/product/quan-dai-nam-double-knit", size="L"):
        """Hỗ trợ thêm một sản phẩm mẫu vào giỏ hàng để sẵn sàng kiểm thử đặt hàng."""
        self.driver.get(product_url)
        time.sleep(3)
        self.dismiss_popups()

        # Chọn size
        size_btns = [b for b in self.driver.find_elements(By.TAG_NAME, "button") if b.is_displayed() and b.text.strip().upper() == size.upper()]
        if size_btns:
            self.driver.execute_script("arguments[0].click();", size_btns[0])
            time.sleep(0.5)

        # Bấm thêm vào giỏ
        add_btns = [b for b in self.driver.find_elements(By.TAG_NAME, "button") if b.is_displayed() and "thêm vào giỏ" in b.text.lower()]
        if add_btns:
            self.driver.execute_script("arguments[0].click();", add_btns[0])
            time.sleep(2.5)

        # Quay lại trang giỏ hàng / thanh toán
        self.load()
        return self

    def fill_shipping_info(self, fullname=None, phone=None, email=None, address=None):
        """Điền thông tin nhận hàng trên form thanh toán."""
        if fullname is not None and self.is_visible(self.FULLNAME_INPUT, timeout=2):
            self.type(self.FULLNAME_INPUT, fullname, clear=True)
            time.sleep(0.3)
        if phone is not None and self.is_visible(self.PHONE_INPUT, timeout=2):
            self.type(self.PHONE_INPUT, phone, clear=True)
            time.sleep(0.3)
        if email is not None and self.is_visible(self.EMAIL_INPUT, timeout=2):
            self.type(self.EMAIL_INPUT, email, clear=True)
            time.sleep(0.3)
        if address is not None and self.is_visible(self.ADDRESS_INPUT, timeout=2):
            self.type(self.ADDRESS_INPUT, address, clear=True)
            time.sleep(0.3)
        return self

    def select_cod_payment(self):
        """Chọn phương thức thanh toán COD (Thanh toán khi nhận hàng)."""
        try:
            cod_els = self.driver.find_elements(*self.COD_PAYMENT_OPTION)
            for el in cod_els:
                if el.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    self.driver.execute_script("arguments[0].click();", el)
                    time.sleep(0.5)
                    return True
        except Exception:
            pass
        return False

    def is_cod_selected(self):
        """Kiểm tra COD có đang được chọn hoặc hiển thị sẵn."""
        try:
            cod_els = self.driver.find_elements(*self.COD_PAYMENT_OPTION)
            return any(el.is_displayed() for el in cod_els)
        except Exception:
            return False

    def get_fullname_value(self):
        """Lấy giá trị trường họ tên."""
        try:
            return self.driver.find_element(*self.FULLNAME_INPUT).get_attribute("value").strip()
        except Exception:
            return ""

    def get_phone_value(self):
        """Lấy giá trị trường số điện thoại."""
        try:
            return self.driver.find_element(*self.PHONE_INPUT).get_attribute("value").strip()
        except Exception:
            return ""

    def get_email_value(self):
        """Lấy giá trị trường email."""
        try:
            return self.driver.find_element(*self.EMAIL_INPUT).get_attribute("value").strip()
        except Exception:
            return ""

    def click_submit_order(self):
        """Bấm nút Đặt hàng (dùng để kiểm tra validation hoặc gửi đơn)."""
        try:
            order_btns = [b for b in self.driver.find_elements(By.TAG_NAME, "button") if "đặt hàng" in b.text.lower() or "đặt hàng" in b.get_attribute("textContent").lower()]
            for b in order_btns:
                if b.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                    self.driver.execute_script("arguments[0].click();", b)
                    time.sleep(1.5)
                    return self
        except Exception:
            pass
        return self

    def get_validation_errors(self):
        """Lấy danh sách các thông báo lỗi hiển thị trên form thanh toán."""
        errors = []
        try:
            elements = self.driver.find_elements(*self.FIELD_ERRORS)
            for el in elements:
                try:
                    if el.is_displayed():
                        t = el.text.strip()
                        if t and t not in errors and len(t) < 100 and not any(w in t.lower() for w in ["sale", "-50%", "newsroom", "coolmate"]):
                            errors.append(t)
                except Exception:
                    pass
        except Exception:
            pass
        return errors
