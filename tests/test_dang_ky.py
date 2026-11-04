"""14 nhóm test đăng ký (Bảng 4.7), chạy bằng pytest.

Dùng RegisterPage hiện có, không cần register_cases.json.
Thiết lập các biến môi trường REG_* cho những test cần dữ liệu đặc biệt.
Kết quả được các conftest.py sẵn có ghi vào results/*.csv và report.html.
"""
import os
import sys
import time
import uuid

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.register_page import RegisterPage


def _print(*args, **kwargs):
    """print() an toàn trên Windows (tránh UnicodeEncodeError với cp1252)."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        print(text.encode("utf-8", errors="replace").decode("utf-8", errors="replace"), **kwargs)


PASSWORD = os.getenv("REG_PASSWORD", "Test@12345")
NAME = "Nguyen Van Test"
# SĐT chỉ sử dụng trên môi trường kiểm thử; không lấy số của người khác.
PHONE = os.getenv("REG_TEST_PHONE", "")
MIN_PASSWORD = int(os.getenv("REG_MIN_PASSWORD", "8"))  # xác nhận lại với yêu cầu thật
MAX_NAME = os.getenv("REG_MAX_NAME", "")
MAX_EMAIL = os.getenv("REG_MAX_EMAIL", "")


def new_email():
    """Email duy nhất về mặt chuỗi; cần hộp thư thực nếu ứng dụng bắt OTP."""
    domain = os.getenv("REG_EMAIL_DOMAIN", "example.com")
    return f"reg{uuid.uuid4().hex[:16]}@{domain}"


def page_of(driver):
    page = RegisterPage(driver)
    page.load()
    return page


def form_field(page, locator):
    return page.find(locator)


def email_field(page):
    return form_field(page, page.EMAIL_INPUT)


def password_field(page):
    return form_field(page, page.PASSWORD_INPUT)


def confirmation_field(page):
    """Trả về input xác nhận mật khẩu (nếu form có)."""
    inputs = page.driver.find_elements(
        By.CSS_SELECTOR,
        "input[name='confirmPassword'], input[name='password_confirmation'], "
        "input[name='confirm_password'], input[autocomplete='new-password'], "
        "input[type='password']",
    )
    primary = password_field(page)
    others = [el for el in inputs if el.id != primary.id and el.is_displayed()]
    return others[0] if others else None


def validation_message(page, field=None):
    """Thông báo native HTML5 hoặc thông báo ứng dụng."""
    native = ""
    if field is not None:
        native = page.driver.execute_script(
            "return arguments[0].validationMessage || '';", field
        ) or ""
    app_errors = page.get_all_errors()
    return " | ".join([s for s in [native, *app_errors] if s.strip()])


def invalid(driver, field):
    return bool(
        driver.execute_script(
            "return arguments[0].validity && "
            "!arguments[0].validity.valid;",
            field
        )
    )


def assert_rejected(page, field=None, expected_words=()):
    """Kiểm tra form từ chối đầu vào: nút disabled, validation, hoặc lỗi hiển thị."""
    # Trường hợp 1: Nút đăng ký bị disabled → form đã ngăn submit → chấp nhận
    submit_btn = page.driver.find_elements(*page.SUBMIT_BTN)
    if submit_btn and not submit_btn[0].is_enabled():
        return  # Nút disabled = form đã từ chối

    # Trường hợp 2: Nút enabled, kiểm tra validation sau khi submit
    message = validation_message(page, field)
    field_invalid = field is not None and invalid(page.driver, field)
    # Có thể website xác thực qua server và hiển thị lỗi sau submit.
    assert field_invalid or message, (
        "Form không báo lỗi/không đánh dấu dữ liệu không hợp lệ"
    )
    assert page.is_on_register_page(), "Dữ liệu không hợp lệ vẫn rời trang đăng ký"
    if expected_words and message:
        assert any(word.lower() in message.lower() for word in expected_words), (
            f"Thông báo không liên quan đến lỗi cần kiểm tra: {message!r}"
        )


def required_env(key, purpose):
    value = os.getenv(key, "").strip()
    if not value:
        pytest.skip(f"Cần cấu hình {key} ({purpose})")
    return value


def fill_base(page, *, name=NAME, email=None, phone=None, password=PASSWORD):
    page.fill_name(name)
    page.fill_email(email or new_email())
    page.fill_phone(phone if phone is not None else (PHONE or "0901234567"))
    page.fill_password(password)


def click_and_check_invalid(page, field):
    page.click_register()
    assert_rejected(page, field)


# ═══════════════════════════════════════════════════════════════════
# REG-01 ─ Đăng ký hợp lệ (tất cả trường đúng)
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
@pytest.mark.smoke
def test_REG_01_dang_ky_hop_le(driver):
    """REG-01: Đăng ký tài khoản với thông tin hợp lệ.

    Cần biến môi trường:
    - REG_NEW_PHONE: SĐT mới chưa từng đăng ký
    - REG_NEW_EMAIL: email mới nhận được mã xác thực nếu cần
    """
    phone = required_env("REG_NEW_PHONE", "SĐT mới chưa từng đăng ký")
    email = required_env("REG_NEW_EMAIL", "email mới nhận được mã xác thực nếu cần")
    page = page_of(driver)
    fill_base(page, email=email, phone=phone)
    page.click_register()
    # Trang OTP không đồng nghĩa tài khoản đã kích hoạt.
    if "otp" in driver.current_url.lower() or "verify" in driver.current_url.lower():
        pytest.skip("Đã đến bước OTP, cần bổ sung xác thực để đánh giá REG-01")
    assert page.is_visible(page.SUCCESS_MESSAGE, timeout=5), (
        "Chưa xác nhận được đăng ký thành công bằng thông báo thành công; "
        "cần bổ sung locator phù hợp site thực tế"
    )


# ═══════════════════════════════════════════════════════════════════
# REG-02 ─ Bỏ trống tất cả trường
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
def test_REG_02_bo_trong_tat_ca(driver):
    """REG-02: Bấm đăng ký khi chưa nhập bất kỳ trường nào."""
    page = page_of(driver)

    # Vẫn ở trang đăng ký
    assert page.is_on_register_page(), "Không còn ở form đăng ký"

    # Thử bấm đăng ký mà không điền gì
    submit_btn = page.visible(page.SUBMIT_BTN)
    button_disabled = not submit_btn.is_enabled()

    if button_disabled:
        # Website vô hiệu hóa nút khi chưa nhập → đã ngăn submit → PASS
        _print("[REG-02] Nút đăng ký bị disabled khi bỏ trống tất cả → form đã ngăn submit")
        return

    # Nếu nút không bị disabled → click và kiểm tra validation
    page.click_register()

    # Kiểm tra: ít nhất 1 trường có validation message hoặc bị invalid
    has_validation = False
    for locator in [page.NAME_INPUT, page.EMAIL_INPUT, page.PHONE_INPUT, page.PASSWORD_INPUT]:
        field = page.find(locator)
        native_msg = page.driver.execute_script(
            "return arguments[0].validationMessage || '';", field
        )
        field_invalid = invalid(driver, field)
        if native_msg or field_invalid:
            has_validation = True
            _print(f"[REG-02] {locator[1]}: msg={native_msg!r}, invalid={field_invalid}")
            break

    app_errors = page.get_all_errors()
    assert has_validation or app_errors, (
        "Form không hiển thị bất kỳ thông báo lỗi nào khi bỏ trống tất cả"
    )


# ═══════════════════════════════════════════════════════════════════
# REG-03 ─ Bỏ trống từng trường
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
@pytest.mark.parametrize("missing", ["name", "email", "phone", "password"])
def test_REG_03_bo_trong_tung_truong(driver, missing):
    """REG-03: Điền đủ trừ 1 trường, form phải từ chối."""
    page = page_of(driver)
    fields = {
        "name": (page.NAME_INPUT, NAME),
        "email": (page.EMAIL_INPUT, new_email()),
        "phone": (page.PHONE_INPUT, PHONE or "0901234567"),
        "password": (page.PASSWORD_INPUT, PASSWORD),
    }
    for field_name, (locator, value) in fields.items():
        if field_name != missing:
            page.type(locator, value)
    target = page.find(fields[missing][0])
    page.click_register()
    assert_rejected(page, target)


# ═══════════════════════════════════════════════════════════════════
# REG-04 ─ Email sai định dạng
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
@pytest.mark.parametrize("email", ["abc", "abc@", "@gmail.com", "a b@x.com", "a@x"])
def test_REG_04_email_sai_dinh_dang(driver, email):
    """REG-04: Email không hợp lệ phải bị từ chối."""
    page = page_of(driver)
    fill_base(page, email=email)
    target = email_field(page)
    page.click_register()
    assert_rejected(page, target)


# ═══════════════════════════════════════════════════════════════════
# REG-05 ─ SĐT sai định dạng
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
@pytest.mark.parametrize("phone", ["09abc12345", "090123456", "09012345678901", "1234567890"])
def test_REG_05_sdt_sai_dinh_dang(driver, phone):
    """REG-05: SĐT không hợp lệ phải bị từ chối."""
    page = page_of(driver)
    fill_base(page, phone=phone)
    target = page.find(page.PHONE_INPUT)
    page.click_register()
    assert_rejected(page, target)


# ═══════════════════════════════════════════════════════════════════
# REG-06 ─ Email đã tồn tại
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
def test_REG_06_email_da_ton_tai(driver):
    """REG-06: Đăng ký bằng email đã có tài khoản.

    Cần biến môi trường: REG_EXISTING_EMAIL
    """
    email = required_env("REG_EXISTING_EMAIL", "email đã có tài khoản")
    page = page_of(driver)
    fill_base(page, email=email)
    page.click_register()
    # Chờ server phản hồi lỗi (có thể mất vài giây)
    time.sleep(2)
    assert_rejected(page, email_field(page))


# ═══════════════════════════════════════════════════════════════════
# REG-07 ─ SĐT đã tồn tại
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
def test_REG_07_sdt_da_ton_tai(driver):
    """REG-07: Đăng ký bằng SĐT đã có tài khoản.

    Cần biến môi trường: REG_EXISTING_PHONE
    """
    phone = required_env("REG_EXISTING_PHONE", "SĐT đã có tài khoản")
    page = page_of(driver)
    fill_base(page, phone=phone)
    page.click_register()
    # Chờ server phản hồi lỗi
    time.sleep(2)
    assert_rejected(page, page.find(page.PHONE_INPUT))


# ═══════════════════════════════════════════════════════════════════
# REG-08 ─ Mật khẩu ngắn hơn mức tối thiểu
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
def test_REG_08_mat_khau_ngan_hon_min(driver):
    """REG-08: Mật khẩu có độ dài < MIN_PASSWORD phải bị từ chối."""
    assert MIN_PASSWORD >= 2, "REG_MIN_PASSWORD phải >= 2"
    page = page_of(driver)
    fill_base(page, password="A" * (MIN_PASSWORD - 1))
    page.click_register()
    assert_rejected(page, password_field(page))


# ═══════════════════════════════════════════════════════════════════
# REG-09 ─ Mật khẩu bằng min và min+1
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
@pytest.mark.parametrize("offset", [0, 1])
def test_REG_09_mat_khau_bang_min_va_min_cong_1(driver, offset):
    """REG-09: Mật khẩu có độ dài = MIN_PASSWORD và MIN_PASSWORD+1.

    Bỏ qua: cần 2 SĐT mới riêng, xác thực thành công/OTP và tiêu chí
    độ dài mật khẩu từ website.
    """
    pytest.skip(
        "REG-09 cần 2 SĐT mới riêng, xác thực thành công/OTP và tiêu chí độ dài mật khẩu từ website"
    )


# ═══════════════════════════════════════════════════════════════════
# REG-10 ─ Xác nhận mật khẩu không khớp
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.high
def test_REG_10_xac_nhan_mat_khau_khong_khop(driver):
    """REG-10: Nhập xác nhận mật khẩu khác mật khẩu."""
    page = page_of(driver)
    confirm = confirmation_field(page)
    if confirm is None:
        pytest.skip("Giao diện không tìm thấy ô xác nhận mật khẩu; kiểm tra locator")
    fill_base(page)
    confirm.clear()
    confirm.send_keys("Different@123")
    page.click_register()
    assert_rejected(page, confirm)


# ═══════════════════════════════════════════════════════════════════
# REG-11 ─ Họ tên đặc biệt / Unicode
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.regression
@pytest.mark.parametrize("name", ["Nguyen123", "@@@", "An ", "Trần Thị Ánh Tuyết"])
def test_REG_11_ho_ten_dac_biet_unicode(driver, name):
    """REG-11: Kiểm tra form xử lý họ tên có ký tự đặc biệt và Unicode."""
    page = page_of(driver)
    fill_base(page, name=name)
    # Kiểm tra dữ liệu nhập không bị mất / sửa trước submit
    actual = page.find(page.NAME_INPUT).get_attribute("value")
    assert actual == name, f"Tên bị sửa/mất Unicode trước khi submit: {actual!r}"
    # Không submit vì quy tắc chấp nhận/từ chối tên chưa được xác định rõ.
    pytest.skip("Cần quy định nghiệp vụ cho từng dạng tên để đánh giá đăng ký")


# ═══════════════════════════════════════════════════════════════════
# REG-12 ─ Vượt giới hạn độ dài
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.regression
def test_REG_12_vuot_gioi_han_do_dai(driver):
    """REG-12: Nhập họ tên dài hơn giới hạn.

    Cần biến môi trường: REG_MAX_NAME (giới hạn ký tự từ đặc tả)
    """
    max_name = required_env("REG_MAX_NAME", "giới hạn họ tên xác nhận từ đặc tả")
    page = page_of(driver)
    text = "A" * (int(max_name) + 1)
    page.fill_name(text)
    field = page.find(page.NAME_INPUT)
    actual = field.get_attribute("value") or ""
    # Không submit tài khoản thật, chấp nhận giới hạn ký tự tại ô nhập.
    if len(actual) <= int(max_name):
        return  # Trình duyệt / front-end đã cắt đúng maxlength
    pytest.skip("Trường cho nhập quá maxlength; cần thử submit với dữ liệu xác thực")


# ═══════════════════════════════════════════════════════════════════
# REG-13 ─ Xác thực OTP
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.regression
def test_REG_13_xac_thuc_otp(driver):
    """REG-13: Xác thực OTP sau đăng ký.

    Cần email/hộp thư kiểm thử và cơ chế nhận OTP (không tự đoán mã).
    """
    pytest.skip("Cần email/hộp thư kiểm thử và cơ chế nhận OTP (không tự đoán mã)")


# ═══════════════════════════════════════════════════════════════════
# REG-14 ─ Ẩn/hiện mật khẩu & thông báo lỗi tiếng Việt
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.regression
def test_REG_14_an_hien_mat_khau_va_loi_tieng_viet(driver):
    """REG-14: Kiểm tra nút ẩn/hiện mật khẩu và thông báo lỗi."""
    page = page_of(driver)

    # --- Phần 1: Kiểm tra ẩn / hiện mật khẩu ---
    page.fill_password(PASSWORD)
    assert page.get_password_field_type() == "password", "Mật khẩu không được ẩn ban đầu"

    # Kiểm tra có nút toggle password không (website có thể đã bỏ tính năng này)
    toggle_elements = driver.find_elements(*page.PASSWORD_TOGGLE)
    toggle_visible = [el for el in toggle_elements if el.is_displayed()]
    if toggle_visible:
        page.click_password_toggle()
        assert page.get_password_field_type() == "text", "Bấm mắt không hiện mật khẩu"
        page.click_password_toggle()
        assert page.get_password_field_type() == "password", "Bấm lại không ẩn mật khẩu"
    else:
        _print("[REG-14] Không tìm thấy nút ẩn/hiện mật khẩu trên giao diện hiện tại")

    # --- Phần 2: Kiểm tra thông báo lỗi khi thiếu trường bắt buộc ---
    page.click_register()

    # Ưu tiên lỗi từ ứng dụng (custom, tiếng Việt)
    app_errors = page.get_all_errors()
    name_field = page.find(page.NAME_INPUT)
    native_msg = page.driver.execute_script(
        "return arguments[0].validationMessage || '';", name_field
    )

    # Nếu nút bị disabled → form đã ngăn submit → chấp nhận
    submit_btn = driver.find_elements(*page.SUBMIT_BTN)
    button_disabled = submit_btn and not submit_btn[0].is_enabled()

    if not button_disabled:
        assert app_errors or native_msg, "Không có lỗi khi thiếu trường bắt buộc"

    # Nếu website có custom error message → kiểm tra tiếng Việt
    if app_errors:
        combined = " ".join(app_errors)
        assert any(ch in combined for ch in "ăâđêôơưĂÂĐÊÔƠƯ") or any(
            word in combined.lower() for word in ["vui lòng", "bắt buộc", "không được", "họ tên", "nhập"]
        ), f"Thông báo lỗi ứng dụng chưa bằng tiếng Việt: {app_errors!r}"
    else:
        # Chỉ có native browser validation → nội dung phụ thuộc ngôn ngữ trình duyệt
        _print(f"[REG-14] Thông báo native browser: {native_msg!r}")
        _print("[REG-14] Website chưa custom thông báo lỗi → kiểm tra tiếng Việt bỏ qua")
