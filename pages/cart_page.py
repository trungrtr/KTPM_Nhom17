"""Page Object: CartPage - Phụ trách: TV4 (Huy) / TV1 (Trung) - Module: CART, VCH.
Tuân thủ kiến trúc POM chuẩn:
1. Locators khai báo ở đầu lớp.
2. Methods là các hành động nghiệp vụ (không assert trong Page Object).
3. Tự động đóng popup nổi và tương thích với React input.
"""
import time
import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pages.base_page import BasePage

logger = logging.getLogger("CoolmateTest.CartPage")


class CartPage(BasePage):
    PATH = "/cart"

    # ---- Locators Giỏ hàng ----
    EMPTY_CART_MESSAGE = (By.XPATH, "//*[contains(text(), 'Giỏ hàng của bạn đang trống') or contains(text(), 'Giỏ hàng của bạn trống') or contains(text(), 'giỏ hàng trống')]")
    CART_ITEM_ROWS = (By.XPATH, "//div[contains(@class, 'cart-item') or contains(@class, 'CartItem') or .//button[contains(., '+') or contains(., '-')]]")
    
    # Nút điều chỉnh số lượng
    QTY_INCREASE_BTN = (By.XPATH, "//button[normalize-space(.)='+' or contains(@class, 'increase')]")
    QTY_DECREASE_BTN = (By.XPATH, "//button[normalize-space(.)='-' or contains(@class, 'decrease')]")
    QTY_INPUT = (By.CSS_SELECTOR, "input[type='number'], input.quantity-input")
    DELETE_ITEM_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'Xóa') or contains(@class, 'remove') or contains(@class, 'delete')]")

    # ---- Locators Voucher ----
    VOUCHER_INPUT = (By.CSS_SELECTOR, "input[name='voucher'], input[placeholder*='mã giảm giá' i], input[placeholder*='voucher' i]")
    APPLY_VOUCHER_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'ÁP DỤNG') or contains(normalize-space(.), 'Áp dụng')]")
    REMOVE_VOUCHER_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'Gỡ mã') or contains(normalize-space(.), 'Bỏ áp dụng') or contains(., 'Gỡ')]")
    VOUCHER_ERROR = (By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'text-red') or contains(text(), 'không hợp lệ') or contains(text(), 'không tồn tại') or contains(text(), 'hết hạn')]")
    
    # ---- Locators Tóm tắt đơn hàng ----
    SUBTOTAL_TEXT = (By.XPATH, "//*[contains(text(), 'Tạm tính')]/following-sibling::* | //*[contains(text(), 'Tạm tính')]/..")
    DISCOUNT_TEXT = (By.XPATH, "//*[contains(text(), 'Giảm giá')]/following-sibling::* | //*[contains(text(), 'Giảm giá')]/..")
    TOTAL_TEXT = (By.XPATH, "//*[contains(text(), 'Tổng tiền') or contains(text(), 'Tổng thanh toán')]/following-sibling::* | //*[contains(text(), 'Tổng tiền')]/..")
    CHECKOUT_BTN = (By.XPATH, "//button[contains(normalize-space(.), 'ĐẶT HÀNG') or contains(normalize-space(.), 'Đặt hàng')]")

    def load(self):
        """Mở trang giỏ hàng và xử lý popup."""
        self.open(self.PATH)
        time.sleep(2)
        self.dismiss_popups()
        return self

    def is_empty_cart(self):
        """Kiểm tra giỏ hàng có đang trống hay không."""
        time.sleep(1)
        source = self.driver.page_source.lower()
        if "trống" in source or "không có sản phẩm" in source:
            return True
        return len(self.driver.find_elements(*self.EMPTY_CART_MESSAGE)) > 0

    def add_sample_product(self, product_url="https://www.coolmate.me/product/quan-dai-nam-double-knit", size="L"):
        """Thêm sản phẩm mẫu vào giỏ hàng."""
        self.driver.get(product_url)
        time.sleep(3)
        self.dismiss_popups()

        # Chọn size
        size_btns = [b for b in self.driver.find_elements(By.TAG_NAME, "button") if b.is_displayed() and b.text.strip().upper() == size.upper()]
        if size_btns:
            self.driver.execute_script("arguments[0].click();", size_btns[0])
            time.sleep(0.5)

        # Bấm thêm vào giỏ bằng ID hoặc text
        add_btns = self.driver.find_elements(By.ID, "product-detail-add-cart")
        if not add_btns:
            add_btns = [b for b in self.driver.find_elements(By.TAG_NAME, "button") if b.is_displayed() and "thêm vào giỏ" in b.text.lower()]
        if add_btns:
            self.driver.execute_script("arguments[0].click();", add_btns[0])
            time.sleep(2.5)

        self.load()
        return self

    def get_cart_item_count(self):
        """Đếm số sản phẩm hiển thị trong giỏ hàng."""
        items = self.driver.find_elements(*self.CART_ITEM_ROWS)
        return len(items)

    def increase_first_item_qty(self):
        """Bấm nút + để tăng số lượng sản phẩm đầu tiên."""
        btns = [b for b in self.driver.find_elements(*self.QTY_INCREASE_BTN) if b.is_displayed()]
        if btns:
            self.driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(1.5)
            return True
        return False

    def decrease_first_item_qty(self):
        """Bấm nút - để giảm số lượng sản phẩm đầu tiên."""
        btns = [b for b in self.driver.find_elements(*self.QTY_DECREASE_BTN) if b.is_displayed()]
        if btns:
            self.driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(1.5)
            return True
        return False

    def remove_first_item(self):
        """Xóa sản phẩm đầu tiên trong giỏ hàng."""
        del_btns = [b for b in self.driver.find_elements(*self.DELETE_ITEM_BTN) if b.is_displayed()]
        if del_btns:
            self.driver.execute_script("arguments[0].click();", del_btns[0])
            time.sleep(2)
            # Nếu có modal xác nhận xóa
            confirm_btns = [b for b in self.driver.find_elements(By.XPATH, "//button[contains(normalize-space(.), 'Xác nhận') or contains(normalize-space(.), 'Đồng ý')]") if b.is_displayed()]
            if confirm_btns:
                self.driver.execute_script("arguments[0].click();", confirm_btns[0])
                time.sleep(1.5)
            return True
        return False

    def enter_voucher_code(self, code):
        """Nhập mã voucher vào ô giảm giá."""
        inputs = [i for i in self.driver.find_elements(*self.VOUCHER_INPUT) if i.is_displayed()]
        if inputs:
            self.type(self.VOUCHER_INPUT, code, clear=True)
            time.sleep(0.5)
            return True
        return False

    def click_apply_voucher(self):
        """Bấm nút Áp dụng voucher."""
        btns = [b for b in self.driver.find_elements(*self.APPLY_VOUCHER_BTN) if b.is_displayed()]
        if btns:
            self.driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(2)
            return True
        return False

    def get_voucher_error_message(self):
        """Lấy thông báo lỗi voucher nếu có."""
        errs = [e.text.strip() for e in self.driver.find_elements(*self.VOUCHER_ERROR) if e.is_displayed() and e.text.strip()]
        return " | ".join(errs)

    def is_checkout_button_available(self):
        """Kiểm tra nút đặt hàng có hiển thị không."""
        btns = [b for b in self.driver.find_elements(*self.CHECKOUT_BTN) if b.is_displayed()]
        return len(btns) > 0
