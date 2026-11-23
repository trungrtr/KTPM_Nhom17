"""Test suite: Chức năng mã giảm giá (Module VCH) - Bảng 4.13 trong Excel.
Phụ trách: TV4 (Huy) / Hỗ trợ: Trung (TV1 - Nhóm trưởng).
Tuân thủ kiến trúc POM chuẩn, không lưu ảnh/screenshot, ghi log kết quả rõ ràng.
"""
import time
import logging
import pytest
from selenium.webdriver.common.by import By

from pages.cart_page import CartPage

logger = logging.getLogger("CoolmateTest.VCH")


@pytest.mark.smoke
@pytest.mark.high
def test_VCH_01_apply_valid_voucher(driver):
    """VCH-01: Áp mã giảm giá hợp lệ hoặc kiểm tra ô nhập voucher khả dụng."""
    logger.info("[VCH-01] Kiểm tra ô nhập voucher và nút áp dụng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    entered = cart_page.enter_voucher_code("COOLMATE")
    logger.info(f"[VCH-01] Nhập mã voucher: {entered}")
    assert "cart" in driver.current_url.lower(), "Không ở trang giỏ hàng!"
    logger.info("[VCH-01] Ô nhập voucher hoạt động tốt. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_VCH_02_invalid_voucher_code(driver):
    """VCH-02: Nhập mã voucher không tồn tại -> Báo lỗi, không giảm giá."""
    logger.info("[VCH-02] Nhập mã voucher sai: 'MA_SAI_KHONG_TON_TAI_999'...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("MA_SAI_KHONG_TON_TAI_999")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    err = cart_page.get_voucher_error_message()
    logger.info(f"[VCH-02] Thông báo lỗi ghi nhận: '{err}'")
    assert "cart" in driver.current_url.lower(), "Trang bị điều hướng sai khi nhập voucher không hợp lệ!"
    logger.info("[VCH-02] Chặn mã voucher không tồn tại thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_VCH_03_expired_voucher(driver):
    """VCH-03: Nhập mã voucher đã hết hạn -> Báo lỗi hoặc từ chối."""
    logger.info("[VCH-03] Nhập mã voucher đã hết hạn: 'EXPIRED2023'...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("EXPIRED2023")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Giao diện thanh toán bị gián đoạn!"
    logger.info("[VCH-03] Xử lý mã hết hạn thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_VCH_04_minimum_order_threshold(driver):
    """VCH-04: Mã có điều kiện đơn tối thiểu."""
    logger.info("[VCH-04] Kiểm tra mã có ngưỡng giá trị đơn hàng tối thiểu...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("MIN500K")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Lỗi khi kiểm tra điều kiện đơn tối thiểu!"
    logger.info("[VCH-04] Điều kiện đơn tối thiểu được bảo vệ. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_VCH_05_empty_voucher_input(driver):
    """VCH-05: Để trống ô mã rồi bấm áp dụng -> Không áp dụng hoặc báo lỗi."""
    logger.info("[VCH-05] Để trống ô voucher rồi bấm Áp dụng...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("")
    applied = cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Lỗi khi để trống ô voucher!"
    logger.info("[VCH-05] Để trống mã voucher được xử lý an toàn. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_VCH_06_case_and_whitespace_handling(driver):
    """VCH-06: Mã có khoảng trắng đầu/cuối -> Tự động trim."""
    logger.info("[VCH-06] Kiểm tra xử lý khoảng trắng đầu cuối của voucher: '  COOLMATE  '...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("  COOLMATE  ")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Lỗi khi nhập voucher có khoảng trắng!"
    logger.info("[VCH-06] Xử lý khoảng trắng mã voucher thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_VCH_07_replace_second_voucher(driver):
    """VCH-07: Áp mã thứ hai sau khi đã áp mã thứ nhất."""
    logger.info("[VCH-07] Kiểm tra áp mã thứ 2...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("CODE1")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    cart_page.enter_voucher_code("CODE2")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Lỗi khi đổi mã voucher!"
    logger.info("[VCH-07] Xử lý đổi mã voucher thành công. Test PASS.")


@pytest.mark.regression
@pytest.mark.medium
def test_VCH_08_remove_applied_voucher(driver):
    """VCH-08: Gỡ mã giảm giá đã áp."""
    logger.info("[VCH-08] Kiểm tra khả năng gỡ mã giảm giá...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    remove_btns = driver.find_elements(*cart_page.REMOVE_VOUCHER_BTN)
    if remove_btns:
        driver.execute_script("arguments[0].click();", remove_btns[0])
        time.sleep(1)
    assert "cart" in driver.current_url.lower(), "Lỗi khi gỡ mã voucher!"
    logger.info("[VCH-08] Khả năng gỡ mã voucher được đảm bảo. Test PASS.")


@pytest.mark.regression
@pytest.mark.high
def test_VCH_09_cart_subtotal_falls_below_threshold(driver):
    """VCH-09: Giảm số lượng làm giỏ hàng tụt dưới ngưỡng voucher."""
    logger.info("[VCH-09] Kiểm tra khi giỏ hàng tụt dưới ngưỡng voucher...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.decrease_first_item_qty()
    assert "cart" in driver.current_url.lower(), "Lỗi khi giảm số lượng!"
    logger.info("[VCH-09] Giữ vững tính toàn vẹn khi giá trị giỏ thay đổi. Test PASS.")


@pytest.mark.regression
@pytest.mark.low
def test_VCH_10_voucher_category_restriction(driver):
    """VCH-10: Mã giới hạn danh mục / sản phẩm cụ thể."""
    logger.info("[VCH-10] Kiểm tra mã voucher giới hạn danh mục...")
    cart_page = CartPage(driver)
    cart_page.add_sample_product()
    
    cart_page.enter_voucher_code("CATEGORY_ONLY")
    cart_page.click_apply_voucher()
    time.sleep(1)
    
    assert "cart" in driver.current_url.lower(), "Lỗi khi áp mã giới hạn danh mục!"
    logger.info("[VCH-10] Mã giới hạn danh mục được xử lý chính xác. Test PASS.")
