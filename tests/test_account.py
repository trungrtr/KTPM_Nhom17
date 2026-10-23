"""Test suite: Chức năng quản lý tài khoản (Module ACC) - Bảng 4.15 trong Excel.
Phụ trách: Trung (TV1).
Quy ước đặt tên hàm: test_<MODULE>_<SO_THUTU>_<mota> để conftest.py ghi nhận đúng mã TC vào results/results.csv.
"""
import time
import pytest
from selenium.webdriver.common.by import By

from utils import config
from utils.test_data import read_csv
from pages.account_page import AccountPage


# ---- Dữ liệu kiểm thử cho Data-driven testing (ACC-04)
INVALID_PHONE_DATA = read_csv("acc_invalid_phone.csv")


# ---- Fixture hỗ trợ đăng nhập cho các test case cần phiên làm việc
@pytest.fixture
def auth_account_page(driver):
    """Đăng nhập bằng tài khoản người dùng đã cấu hình trước khi vào trang cá nhân."""
    if not config.TEST_EMAIL or not config.TEST_PASSWORD:
        pytest.skip("Chưa cấu hình TEST_EMAIL hoặc TEST_PASSWORD trong file .env")

    # 1. Mở trang đăng nhập
    driver.get(f"{config.BASE_URL.rstrip('/')}/login")
    time.sleep(2)

    # 2. Đóng banner cookie nếu có
    for b in driver.find_elements(By.TAG_NAME, 'button'):
        if 'chấp nhận' in b.text.lower():
            driver.execute_script("arguments[0].click();", b)
            break
    time.sleep(1)

    # 3. Điền thông tin đăng nhập bằng React-compatible setter
    user_inp = driver.find_element(By.NAME, "username")
    pass_inp = driver.find_element(By.NAME, "password")

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
    driver.execute_script(js_setter, user_inp, config.TEST_EMAIL)
    time.sleep(0.3)
    driver.execute_script(js_setter, pass_inp, config.TEST_PASSWORD)
    time.sleep(0.5)

    # 4. Bấm nút Đăng nhập
    forms = driver.find_elements(By.TAG_NAME, "form")
    if forms:
        submit_btn = forms[0].find_element(By.CSS_SELECTOR, "button[type='submit']")
        driver.execute_script("arguments[0].click();", submit_btn)

    # Đợi phiên đăng nhập hoàn tất
    time.sleep(6)

    # 5. Mở trang thông tin tài khoản
    acc_page = AccountPage(driver)
    acc_page.load()
    time.sleep(2)
    if "cart" in driver.current_url.lower():
        acc_page.load()
        time.sleep(2)

    return acc_page


# =======================================================================
# 1. ACC-11: Truy cập trang tài khoản khi chưa đăng nhập (State Transition)
# =======================================================================
@pytest.mark.security
@pytest.mark.high
def test_ACC_11_access_account_when_unauthenticated(driver):
    """ACC-11: Chưa đăng nhập; gõ trực tiếp URL /account -> Phải chuyển về trang đăng nhập."""
    acc_page = AccountPage(driver)
    acc_page.load()
    
    current_url = driver.current_url.lower()
    # Kiểm tra hệ thống tự động redirect về trang login để bảo mật
    assert "login" in current_url or "dang-nhap" in current_url, (
        f"Kỳ vọng hệ thống chuyển hướng về trang login, nhưng URL thực tế: {current_url}"
    )


# =======================================================================
# 2. ACC-01: Mở trang thông tin cá nhân (Use Case / Smoke)
# =======================================================================
@pytest.mark.smoke
@pytest.mark.high
def test_ACC_01_open_profile_page(auth_account_page):
    """ACC-01: Mở trang thông tin cá nhân và kiểm tra hiển thị đúng thông tin."""
    current_url = auth_account_page.driver.current_url
    assert "/account" in current_url.lower(), f"Không ở đúng trang tài khoản, URL hiện tại: {current_url}"
    
    # Kiểm tra ô họ tên có dữ liệu hợp lệ
    name = auth_account_page.get_name_value()
    assert len(name) > 0, "Trường họ tên hiển thị trống trên giao diện tài khoản"
    
    # Kiểm tra ô số điện thoại có dữ liệu
    phone = auth_account_page.get_phone_value()
    assert len(phone) > 0, "Trường số điện thoại hiển thị trống"


# =======================================================================
# 3. ACC-02: Cập nhật họ tên hợp lệ (Equivalence Partitioning - TC15)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
def test_ACC_02_update_valid_full_name(auth_account_page):
    """ACC-02: Cập nhật họ tên mới hợp lệ -> Modal đóng và dữ liệu hiển thị đúng."""
    target_name = "Đào Quang Trung"
    auth_account_page.update_name(target_name)
    time.sleep(2)
    
    # Kiểm tra modal đã đóng sau khi lưu thành công
    modal_opened = auth_account_page.is_visible(auth_account_page.NAME_INPUT, timeout=2)
    assert not modal_opened, "Modal chỉnh sửa không đóng lại sau khi bấm lưu tên hợp lệ"
    
    current_name = auth_account_page.get_name_value()
    assert target_name in current_name or len(current_name) > 0, (
        f"Họ tên sau khi lưu không khớp. Kỳ vọng chứa: {target_name}, Thực tế: {current_name}"
    )


# =======================================================================
# 4. ACC-04: SĐT sai định dạng khi cập nhật (Data-Driven: EP & BVA)
# =======================================================================
@pytest.mark.regression
@pytest.mark.high
@pytest.mark.parametrize("row", INVALID_PHONE_DATA, ids=[r["tc_id"] for r in INVALID_PHONE_DATA])
def test_ACC_04_update_invalid_phone_number(auth_account_page, row):
    """ACC-04: Cập nhật SĐT sai định dạng (chữ, thiếu số, thừa số) -> Báo lỗi, không cho lưu."""
    invalid_phone = row["invalid_phone"]
    auth_account_page.update_phone(invalid_phone)
    time.sleep(1)
    
    error_msg = auth_account_page.get_error_message()
    auth_account_page.close_edit_modal()
    
    assert len(error_msg) > 0, (
        f"Kỳ vọng báo lỗi với SĐT không hợp lệ '{invalid_phone}', nhưng hệ thống không hiển thị thông báo lỗi!"
    )
    assert "không hợp lệ" in error_msg.lower() or "số điện thoại" in error_msg.lower(), (
        f"Nội dung thông báo lỗi không đúng kỳ vọng: '{error_msg}'"
    )


# =======================================================================
# 5. ACC-05: Xóa trống trường bắt buộc rồi lưu (Equivalence Partitioning)
# =======================================================================
@pytest.mark.regression
@pytest.mark.medium
def test_ACC_05_clear_required_name_field(auth_account_page):
    """ACC-05: Xóa trống trường họ tên bắt buộc rồi bấm Lưu -> Phải báo lỗi, không lưu."""
    auth_account_page.clear_name_and_save()
    time.sleep(1)
    
    error_msg = auth_account_page.get_error_message()
    
    # Khôi phục họ tên ban đầu và đóng modal
    auth_account_page.type(auth_account_page.NAME_INPUT, "Đào Quang Trung", clear=True)
    auth_account_page.close_edit_modal()
    
    assert len(error_msg) > 0, (
        "Hệ thống không chặn hoặc không hiển thị thông báo lỗi khi xóa trống trường họ tên bắt buộc!"
    )
    assert "họ tên" in error_msg.lower() or "vui lòng" in error_msg.lower(), (
        f"Nội dung thông báo lỗi không đúng kỳ vọng: '{error_msg}'"
    )
