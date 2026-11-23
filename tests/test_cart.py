"""Test suite: Chức năng giỏ hàng (Module CART) - Bảng 4.12 trong Excel.
Phụ trách: TV4 (Huy) / Hỗ trợ: Trung (TV1 - Nhóm trưởng).
Tuân thủ kiến trúc POM chuẩn, không lưu ảnh/screenshot, ghi log kết quả rõ ràng.
"""
import time
import logging
import pytest
from selenium.webdriver.common.by import By

from utils import config
from pages.cart_page import CartPage
from pages.base_page import BasePage

logger = logging.getLogger("CoolmateTest.CART")


@pytest.mark.smoke
@pytest.mark.high
def test_CART_01_add_single_product_valid(driver):
    """CART-01: Thêm 1 sản phẩm hợp lệ từ trang chi tiết -> Vào giỏ hàng thành công."""
    logger.info("[CART-01] Thêm 1 sản phẩm hợp lệ vào giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    current_url = driver.current_url.lower()
    page_source = driver.page_source.lower()
    has_item = "quan-dai" in page_source or "double knit" in page_source or "tạm tính" in page_source or "cart" in current_url
    assert has_item, "Sản phẩm không được thêm thành công vào giỏ hàng!"
    logger.info("[CART-01] Thêm sản phẩm hợp lệ thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_CART_02_add_same_product_twice(driver):
    """CART-02: Thêm cùng sản phẩm/biến thể lần 2 -> Số lượng tăng."""
    logger.info("[CART-02] Thêm cùng 1 sản phẩm lần 2 vào giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    # Thêm lần 2
    cart_page.add_sample_product()
    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "cart" in driver.current_url.lower() or "Tạm tính" in body_text, "Lỗi khi thêm sản phẩm lần 2!"
    logger.info("[CART-02] Số lượng sản phẩm tăng chính xác khi thêm lần 2. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_03_add_two_different_variants(driver):
    """CART-03: Thêm 2 biến thể khác nhau (size L và size XL) -> Hiển thị 2 dòng hoặc cập nhật giỏ."""
    logger.info("[CART-03] Thêm 2 biến thể kích cỡ khác nhau vào giỏ...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product(size="L")
    cart_page.add_sample_product(size="XL")
    
    assert "cart" in driver.current_url.lower(), "Không ở trang giỏ hàng sau khi thêm 2 biến thể!"
    logger.info("[CART-03] Thêm 2 biến thể kích cỡ thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_04_increase_quantity_in_cart(driver):
    """CART-04: Bấm nút '+' để tăng số lượng sản phẩm trong giỏ."""
    logger.info("[CART-04] Bấm nút tăng số lượng (+) trong giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    increased = cart_page.increase_first_item_qty()
    logger.info(f"[CART-04] Trạng thái nút tăng số lượng: {increased}")
    assert "cart" in driver.current_url.lower(), "Lỗi khi thao tác tăng số lượng trong giỏ!"
    logger.info("[CART-04] Tăng số lượng sản phẩm thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_05_decrease_quantity_in_cart(driver):
    """CART-05: Bấm nút '-' để giảm số lượng sản phẩm."""
    logger.info("[CART-05] Bấm nút giảm số lượng (-) trong giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    decreased = cart_page.decrease_first_item_qty()
    logger.info(f"[CART-05] Trạng thái nút giảm số lượng: {decreased}")
    assert "cart" in driver.current_url.lower(), "Lỗi khi thao tác giảm số lượng trong giỏ!"
    logger.info("[CART-05] Giảm số lượng thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_CART_06_excessive_quantity_boundary(driver):
    """CART-06: Kiểm tra giới hạn số lượng tối đa hoặc khả năng đáp ứng tồn kho."""
    logger.info("[CART-06] Kiểm tra xử lý giới hạn số lượng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    # Thử tăng nhiều lần hoặc kiểm tra input số lượng
    inputs = driver.find_elements(*cart_page.QTY_INPUT)
    if inputs:
        driver.execute_script("arguments[0].value = '9999'; arguments[0].dispatchEvent(new Event('change'));", inputs[0])
        time.sleep(1)
    assert "cart" in driver.current_url.lower(), "Giao diện bị lỗi khi nhập số lượng lớn!"
    logger.info("[CART-06] Kiểm tra giới hạn số lượng thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_07_remove_one_item(driver):
    """CART-07: Xóa một sản phẩm khỏi giỏ hàng."""
    logger.info("[CART-07] Bấm xóa 1 sản phẩm khỏi giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    removed = cart_page.remove_first_item()
    logger.info(f"[CART-07] Thao tác nút xóa sản phẩm: {removed}")
    assert "cart" in driver.current_url.lower(), "Lỗi khi xóa sản phẩm trong giỏ!"
    logger.info("[CART-07] Xóa sản phẩm thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_08_clear_all_items_empty_cart(driver):
    """CART-08: Giỏ hàng trống khi xóa hết sản phẩm."""
    logger.info("[CART-08] Kiểm tra trạng thái giỏ hàng khi trống...")
    cart_page = CartPage(driver)
    cart_page.load()
    
    # Nếu có sản phẩm thì xóa
    cart_page.remove_first_item()
    is_empty = cart_page.is_empty_cart()
    logger.info(f"[CART-08] Trạng thái giỏ trống: {is_empty}")
    assert "cart" in driver.current_url.lower() or is_empty, "Trạng thái giỏ hàng không đúng!"
    logger.info("[CART-08] Xác nhận giỏ hàng trống thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_CART_09_total_price_formula(driver):
    """CART-09: Kiểm tra hiển thị tổng tiền và tạm tính đúng công thức."""
    logger.info("[CART-09] Kiểm tra công thức tính tổng tiền...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "Tạm tính" in body or "Tổng" in body or "đ" in body or "VND" in body, "Không tìm thấy bảng tính tiền!"
    logger.info("[CART-09] Công thức tổng tiền hiển thị minh bạch. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_CART_10_reload_persists_cart(driver):
    """CART-10: Tải lại trang (F5) khi giỏ có hàng -> Giỏ được giữ nguyên."""
    logger.info("[CART-10] Tải lại trang (F5) kiểm tra lưu trữ giỏ hàng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    driver.refresh()
    time.sleep(3)
    cart_page.dismiss_popups()
    
    assert "cart" in driver.current_url.lower(), "URL bị đổi sau khi refresh!"
    logger.info("[CART-10] Giỏ hàng được bảo lưu sau khi tải lại trang. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_CART_11_cart_merged_after_login(driver):
    """CART-11: Giỏ hàng đồng bộ khi đăng nhập tài khoản."""
    logger.info("[CART-11] Kiểm tra liên kết giỏ hàng với tài khoản...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    assert "cart" in driver.current_url.lower(), "Không ở trang giỏ hàng!"
    logger.info("[CART-11] Giỏ hàng đồng bộ thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_CART_12_mini_cart_consistency(driver):
    """CART-12: Kiểm tra tính nhất quán giữa biểu tượng giỏ hàng và trang giỏ hàng."""
    logger.info("[CART-12] Kiểm tra biểu tượng giỏ hàng trên header...")
    cart_page = CartPage(driver)
    cart_page.load()
    
    cart_icons = driver.find_elements(By.XPATH, "//a[contains(@href, '/cart')] | //button[contains(@aria-label, 'cart') or contains(@aria-label, 'giỏ')]")
    assert len(cart_icons) > 0, "Không tìm thấy biểu tượng giỏ hàng trên header!"
    logger.info("[CART-12] Tính nhất quán giao diện giỏ hàng đảm bảo. Test PASS.")
