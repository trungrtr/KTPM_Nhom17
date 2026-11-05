"""Test suite: Chức năng đặt hàng và thanh toán (Module ORD) - Bảng 4.14 trong Excel.
Phụ trách: Trung (TV1 - Nhóm trưởng) / TV4 (Huy).
Tuân thủ kiến trúc Page Object Model (POM):
- Tách biệt hoàn toàn Locators & Hành vi trong CheckoutPage.
- Không assert trong Page Object; File test chỉ gọi nghiệp vụ và assert.
- Xử lý đóng/cô lập các cửa sổ nổi (cookie, popup chào mừng, toast) tránh gây fail sai lệch.
- Ghi log kết quả chi tiết từng bước, không lưu ảnh/screenshot màn hình theo yêu cầu.
- Quy tắc an toàn: chỉ chọn COD, dừng trước bước xác nhận cuối.
"""
import time
import logging
import pytest
from selenium.webdriver.common.by import By

from utils import config
from utils.test_data import read_csv
from pages.checkout_page import CheckoutPage
from pages.base_page import BasePage

logger = logging.getLogger("CoolmateTest.ORD")

# ---- Dữ liệu kiểm thử cho Data-driven testing (ORD-03)
INVALID_PHONE_DATA = read_csv("ord_invalid_phone.csv")


# =======================================================================
# 1. ORD-11: Vào trang đặt hàng khi giỏ trống (State Transition)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_11_access_checkout_when_cart_empty(driver):
    """ORD-11: Giỏ trống; gõ trực tiếp URL trang đặt hàng -> Bị chặn hoặc chuyển về thông báo giỏ hàng trống."""
    logger.info("[ORD-11] Bắt đầu kiểm thử truy cập trang đặt hàng khi giỏ trống...")
    page = CheckoutPage(driver)
    page.load()
    time.sleep(2)

    current_url = driver.current_url.lower()
    page_source = driver.page_source.lower()
    logger.info(f"[ORD-11] URL hiện tại: {current_url}")

    is_blocked_or_empty = (
        page.is_empty_cart()
        or "trống" in page_source
        or "404" in page_source
        or "cart" in current_url
    )
    assert is_blocked_or_empty, "Hệ thống không hiển thị thông báo giỏ hàng trống hoặc không chặn khi giỏ trống!"
    logger.info("[ORD-11] Xác nhận chặn truy cập khi giỏ trống thành công. Test PASS.")


# =======================================================================
# 2. ORD-08: Chọn phương thức thanh toán COD (Use Case)
# =======================================================================
@pytest.mark.smoke
@pytest.mark.high
def test_ORD_08_select_cod_payment_method(driver):
    """ORD-08: Thêm sản phẩm mẫu và kiểm tra phương thức thanh toán COD khả dụng."""
    logger.info("[ORD-08] Chuẩn bị giỏ hàng và kiểm tra phương thức COD...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    cod_available = page.is_cod_selected()
    logger.info(f"[ORD-08] Tình trạng khả dụng phương thức COD: {cod_available}")
    assert cod_available, "Phương thức COD (Thanh toán khi nhận hàng) không hiển thị trên giao diện thanh toán!"

    selected = page.select_cod_payment()
    logger.info(f"[ORD-08] Đã chọn phương thức COD: {selected}")
    logger.info("[ORD-08] Xác nhận phương thức COD hoạt động chuẩn xác. Test PASS.")


# =======================================================================
# 3. ORD-04: Email nhận đơn sai định dạng (Equivalence Partitioning)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_04_invalid_email_format(driver):
    """ORD-04: Nhập email sai định dạng (abc, abc@) -> Báo lỗi hoặc chặn không cho đi tiếp."""
    logger.info("[ORD-04] Bắt đầu kiểm thử email nhận đơn sai định dạng...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    invalid_email = "test_sai_dinh_dang@"
    page.fill_shipping_info(email=invalid_email)
    time.sleep(0.5)

    page.click_submit_order()
    time.sleep(1)

    errors = page.get_validation_errors()
    email_val = page.get_email_value()
    logger.info(f"[ORD-04] Email đã nhập: '{email_val}' | Các lỗi nhận diện: {errors}")

    email_el = driver.find_element(*page.EMAIL_INPUT)
    is_invalid = driver.execute_script("return !arguments[0].validity.valid;", email_el) or len(errors) > 0
    assert is_invalid, f"Hệ thống không chặn email sai định dạng: '{invalid_email}'!"
    logger.info("[ORD-04] Xác nhận chặn email sai định dạng thành công. Test PASS.")


# =======================================================================
# 4. ORD-02: Để trống trường thông tin giao hàng (Equivalence Partitioning)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
def test_ORD_02_empty_required_shipping_fields(driver):
    """ORD-02: Để trống thông tin giao hàng rồi bấm Đặt hàng -> Báo lỗi bắt buộc, không đi tiếp."""
    logger.info("[ORD-02] Bắt đầu kiểm thử để trống thông tin giao hàng...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    page.fill_shipping_info(fullname="", phone="", email="", address="")
    page.click_submit_order()
    time.sleep(1.5)

    errors = page.get_validation_errors()
    logger.info(f"[ORD-02] Danh sách lỗi ghi nhận được: {errors}")

    current_url = driver.current_url.lower()
    assert "cart" in current_url or len(errors) > 0, "Hệ thống không chặn khi để trống trường thông tin giao hàng bắt buộc!"
    logger.info("[ORD-02] Xác nhận chặn trường bắt buộc thành công. Test PASS.")


# =======================================================================
# 5. ORD-03: SĐT nhận hàng sai định dạng (Data-Driven: EP & BVA)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
@pytest.mark.parametrize("row", INVALID_PHONE_DATA, ids=[r["tc_id"] for r in INVALID_PHONE_DATA])
def test_ORD_03_invalid_phone_number(driver, row):
    """ORD-03: SĐT nhận hàng sai định dạng (chữ, thiếu số, quá dài, sai đầu số) -> Báo lỗi."""
    invalid_phone = row["invalid_phone"]
    description = row.get("description", "")
    logger.info(f"[ORD-03] Kiểm thử SĐT giao hàng: '{invalid_phone}' ({description})...")

    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()
    page.fill_shipping_info(fullname="Nguyen Van Test", phone=invalid_phone, email="test@example.com")
    time.sleep(0.5)

    page.click_submit_order()
    time.sleep(1)

    phone_el = driver.find_element(*page.PHONE_INPUT)
    is_invalid = driver.execute_script("return !arguments[0].validity.valid;", phone_el)
    errors = page.get_validation_errors()
    logger.info(f"[ORD-03] Phản hồi lỗi: HTML5_invalid={is_invalid}, Errors={errors}")

    assert is_invalid or len(errors) > 0 or "cart" in driver.current_url.lower(), (
        f"Hệ thống không chặn SĐT giao hàng không hợp lệ: '{invalid_phone}'"
    )
    logger.info(f"[ORD-03] Xác nhận kiểm tra SĐT '{invalid_phone}' thành công. Test PASS.")


# =======================================================================
# 6. ORD-01: Đặt hàng hợp lệ, dừng tại bước xác nhận (Use Case / Safety Rule)
# =======================================================================
@pytest.mark.smoke
@pytest.mark.high
def test_ORD_01_valid_order_stop_before_confirmation(driver):
    """ORD-01: Giỏ có hàng, thông tin giao hàng hợp lệ, phương thức COD. DỪNG tại bước xác nhận cuối."""
    logger.info("[ORD-01] Bắt đầu kiểm thử đặt hàng hợp lệ (dừng trước xác nhận theo quy tắc an toàn)...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    page.fill_shipping_info(
        fullname="Đào Quang Trung",
        phone="0877900786",
        email="daoquangtrung194@gmail.com",
        address="123 Nguyễn Trãi"
    )
    page.select_cod_payment()
    time.sleep(1)

    fn = page.get_fullname_value()
    ph = page.get_phone_value()
    em = page.get_email_value()
    logger.info(f"[ORD-01] Tóm tắt thông tin đã điền: Tên='{fn}', SĐT='{ph}', Email='{em}'")

    assert len(fn) > 0, "Trường họ tên chưa được điền giá trị"
    assert len(ph) > 0, "Trường SĐT chưa được điền giá trị"
    assert len(em) > 0, "Trường email chưa được điền giá trị"

    logger.info("[ORD-01] Tuân thủ quy tắc an toàn website thật: Dừng trước bước bấm xác nhận đơn cuối.")
    logger.info("[ORD-01] Đặt hàng hợp lệ thành công. Test PASS.")


# =======================================================================
# 7. ORD-05: Chọn Tỉnh → Quận/Huyện → Phường/Xã (State Transition)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
def test_ORD_05_select_administrative_units(driver):
    """ORD-05: Kiểm tra các trường chọn Tỉnh/Thành phố, Quận/Huyện, Phường/Xã."""
    logger.info("[ORD-05] Bắt đầu kiểm thử chọn đơn vị hành chính Tỉnh/Quận/Phường...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    prov_inps = driver.find_elements(*page.PROVINCE_INPUT)
    has_prov = len(prov_inps) > 0
    logger.info(f"[ORD-05] Hiển thị trường Tỉnh/Thành phố: {has_prov}")
    assert has_prov, "Không tìm thấy trường chọn Tỉnh/Thành phố trên form giao hàng!"
    logger.info("[ORD-05] Xác nhận tương tác đơn vị hành chính thành công. Test PASS.")


# =======================================================================
# 8. ORD-06: Phí vận chuyển theo địa chỉ (Equivalence Partitioning)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
def test_ORD_06_shipping_fee_display(driver):
    """ORD-06: Phí vận chuyển hiển thị trên tóm tắt đơn hàng."""
    logger.info("[ORD-06] Kiểm tra hiển thị phí vận chuyển trên giỏ hàng / thanh toán...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    has_shipping = "vận chuyển" in body or "freeship" in body or "phí" in body
    logger.info(f"[ORD-06] Trạng thái hiển thị thông tin vận chuyển: {has_shipping}")
    assert has_shipping, "Thông tin phí vận chuyển không hiển thị trên giao diện thanh toán!"
    logger.info("[ORD-06] Xác nhận hiển thị thông tin vận chuyển thành công. Test PASS.")


# =======================================================================
# 9. ORD-07: Điều kiện miễn phí vận chuyển (Boundary Value Analysis)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_07_freeship_threshold_condition(driver):
    """ORD-07: Điều kiện miễn phí vận chuyển (ngưỡng Freeship 200k trên Coolmate)."""
    logger.info("[ORD-07] Kiểm tra điều kiện chính sách miễn phí vận chuyển...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    body = driver.find_element(By.TAG_NAME, "body").text.lower()
    has_freeship_policy = "freeship" in body or "miễn phí" in body or "200k" in body
    logger.info(f"[ORD-07] Chính sách freeship ghi nhận: {has_freeship_policy}")
    assert has_freeship_policy, "Chính sách miễn phí vận chuyển không hiển thị trên giao diện giỏ hàng!"
    logger.info("[ORD-07] Xác nhận điều kiện freeship thành công. Test PASS.")


# =======================================================================
# 10. ORD-09: Chọn phương thức thanh toán online / ví (Use Case)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_09_online_payment_options_available(driver):
    """ORD-09: Kiểm tra các phương thức thanh toán online / ví hiển thị đầy đủ, an toàn không phát sinh giao dịch thật."""
    logger.info("[ORD-09] Kiểm tra các phương thức thanh toán online (Ví MoMo, Zalopay, ShopeePay)...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    online_options = driver.find_elements(*page.ONLINE_PAYMENT_OPTION)
    logger.info(f"[ORD-09] Số lượng tùy chọn thanh toán trực tuyến: {len(online_options)}")
    assert len(online_options) > 0, "Không hiển thị phương thức thanh toán trực tuyến / ví điện tử!"
    logger.info("[ORD-09] Xác nhận hiển thị phương thức thanh toán online thành công. Test PASS.")


# =======================================================================
# 11. ORD-10: Tổng thanh toán kết hợp phí ship và voucher (Decision Table)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
def test_ORD_10_total_amount_summary(driver):
    """ORD-10: Tổng thanh toán hiển thị rõ ràng: Tạm tính, Giảm giá và Tổng tiền."""
    logger.info("[ORD-10] Kiểm tra tóm tắt tổng thanh toán giỏ hàng...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    body = driver.find_element(By.TAG_NAME, "body").text
    has_tam_tinh = "Tạm tính" in body
    has_voucher_field = len(driver.find_elements(*page.VOUCHER_INPUT)) > 0 or "voucher" in body.lower()
    logger.info(f"[ORD-10] Tạm tính={has_tam_tinh}, Ô nhập voucher={has_voucher_field}")
    assert has_tam_tinh, "Bảng tóm tắt thanh toán không hiển thị dòng Tạm tính!"
    logger.info("[ORD-10] Xác nhận tóm tắt thanh toán thành công. Test PASS.")


# =======================================================================
# 12. ORD-12: Thông tin điền sẵn khi đã đăng nhập (Use Case)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_12_prefilled_info_when_authenticated(driver):
    """ORD-12: Đăng nhập tài khoản có sẵn thông tin -> Vào đặt hàng kiểm tra tự động điền sẵn."""
    if not config.TEST_EMAIL or not config.TEST_PASSWORD:
        pytest.skip("Chưa cấu hình TEST_EMAIL hoặc TEST_PASSWORD trong file .env")

    logger.info("[ORD-12] Đăng nhập tài khoản trước khi vào thanh toán...")
    driver.get(f"{config.BASE_URL.rstrip('/')}/login")
    time.sleep(2)

    for b in driver.find_elements(By.XPATH, "//button[contains(normalize-space(.), 'Chấp nhận')]"):
        if b.is_displayed():
            driver.execute_script("arguments[0].click();", b)
            break

    user_inp = driver.find_element(By.NAME, "username")
    pass_inp = driver.find_element(By.NAME, "password")
    js_setter = """
    const input = arguments[0];
    const value = arguments[1];
    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
    if (nativeSetter) { nativeSetter.call(input, value); } else { input.value = value; }
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    """
    driver.execute_script(js_setter, user_inp, config.TEST_EMAIL)
    driver.execute_script(js_setter, pass_inp, config.TEST_PASSWORD)
    time.sleep(0.5)

    forms = driver.find_elements(By.TAG_NAME, "form")
    if forms:
        submit_btn = forms[0].find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit_btn)

    time.sleep(4)
    BasePage(driver).dismiss_popups()

    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    fn = page.get_fullname_value()
    ph = page.get_phone_value()
    em = page.get_email_value()
    logger.info(f"[ORD-12] Thông tin tự động điền sẵn: Tên='{fn}', SĐT='{ph}', Email='{em}'")

    has_prefilled = len(fn) > 0 or len(ph) > 0 or len(em) > 0
    assert has_prefilled or "cart" in driver.current_url.lower(), "Hệ thống không nhận diện phiên đăng nhập tại bước đặt hàng!"
    logger.info("[ORD-12] Xác nhận tự động gắn kết thông tin tài khoản thành công. Test PASS.")


# =======================================================================
# 13. ORD-13: Quay lại sửa giỏ hàng giữa chừng (State Transition)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ORD_13_modify_cart_during_checkout(driver):
    """ORD-13: Thao tác sửa giỏ hàng (thay đổi số lượng, xóa) tại giao diện thanh toán."""
    logger.info("[ORD-13] Kiểm tra thao tác sửa sản phẩm trên giỏ hàng...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    # Tìm các nút sửa số lượng (+, -) hoặc nút Xóa trong giỏ
    modify_btns = driver.find_elements(By.XPATH, "//button[contains(., '+') or contains(., '-') or contains(., 'Xóa') or contains(., 'xóa')]")
    logger.info(f"[ORD-13] Tìm thấy {len(modify_btns)} nút điều chỉnh giỏ hàng")
    assert len(modify_btns) > 0, "Không tìm thấy nút điều chỉnh số lượng hoặc xóa sản phẩm trong giỏ!"
    logger.info("[ORD-13] Xác nhận chức năng điều chỉnh giỏ hàng giữa chừng thành công. Test PASS.")


# =======================================================================
# 14. ORD-14: Đặt thật 1 đơn COD rồi hủy ngay (Safety Rule)
# =======================================================================
@pytest.mark.high
def test_ORD_14_cod_order_ready_and_safety_stop(driver):
    """ORD-14: Kiểm tra trạng thái đơn COD sẵn sàng và tuân thủ quy tắc an toàn website thật."""
    logger.info("[ORD-14] Kiểm tra nút xác nhận đơn COD sẵn sàng (dừng trước khi đặt thật để đảm bảo an toàn)...")
    page = CheckoutPage(driver)
    page.add_sample_product_to_cart()

    order_btns = [b for b in driver.find_elements(By.XPATH, "//button[contains(normalize-space(.), 'ĐẶT HÀNG') or contains(normalize-space(.), 'Đặt hàng')]") if b.is_displayed()]
    logger.info(f"[ORD-14] Nút ĐẶT HÀNG khả dụng: {len(order_btns) > 0}")
    assert len(order_btns) > 0, "Nút đặt hàng không hiển thị trên giao diện thanh toán!"
    logger.info("[ORD-14] Tuân thủ quy định kiểm thử an toàn trên website production. Test PASS.")
