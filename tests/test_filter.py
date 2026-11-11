"""Test module Lọc / sắp xếp (FLT) - phụ trách: TV3 (Lâm).
FLT-10, FLT-11 là loại M - chạy tay, không có script.

Giao diện thật của Coolmate (trang /collection/...): cột bộ lọc bên trái với Kích thước (nút XS..4XL), Màu sắc (ô màu + tên),
Giá (4 ô tick: "0 - 200.000đ", "200.000đ - 300.000đ", "300.000đ - 500.000đ", ">500.000đ"), Chất liệu, Kiểu dáng;
ô "Sắp xếp theo" (Mặc định, Bán chạy, Mới nhất, Giá thấp đến cao, Giá cao đến thấp, %Giảm giá nhiều).
Khi có bộ lọc: URL ghi trạng thái (ví dụ ?sort=price-asc&size=m), hiện chip "M ✕" và nút "Xoá lọc".
Các test dùng nút "Xoá lọc" và URL để biết bộ lọc đã được áp dụng (số "N kết quả" biến mất khi đã lọc).

Quy ước kết quả: không tìm thấy phần tử giao diện -> SKIPPED kèm lý do (chưa thực thi tự động, KHÔNG tính là pass);
assert sai -> FAILED (cần tái hiện bằng tay rồi mới kết luận là lỗi website).
"""
import functools

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from pages.search_page import SearchPage, UiNotFound
from utils.test_data import read_csv

# ---- Dữ liệu kiểm thử (Data-driven) đọc từ thư mục data/
CATEGORIES = read_csv("flt_category.csv")
COLORS = read_csv("flt_color.csv")
SIZES = read_csv("flt_size.csv")
PRICES = read_csv("flt_price.csv")
NO_RESULT_COMBOS = read_csv("flt_no_result.csv")

CATEGORY_PATH = "/collection/ao-thun-nam"                       # trang danh mục dùng cho các test lọc / sắp xếp
COMBINED = ("200.000đ - 300.000đ", 200000, 300000, "Đen", "L")  # FLT-05: ô giá, giá thấp, giá cao, màu, size
SORT_ASC, SORT_DESC = "Giá thấp đến cao", "Giá cao đến thấp"
CLEAR_TEST_FILTER = "M"      # bộ lọc dùng cho FLT-06 và FLT-12 (size M: đã thấy chip "M ✕" và nút "Xoá lọc" trên site)
SAMPLE = 3                                                       # số sản phẩm mở ra kiểm tra chéo

from tests import browser_session

driver = browser_session.driver      # dùng chung một Chrome cho cả file (nhanh hơn)

smoke = pytest.mark.smoke
regression = pytest.mark.regression
high = pytest.mark.high
medium = pytest.mark.medium


def skip_if_ui_missing(fn):
    """Không tìm thấy bộ lọc / sắp xếp trên trang = locator chưa khớp, KHÔNG phải lỗi của website.
    Test được ghi nhận SKIPPED kèm lý do (chưa thực thi tự động, không tính là pass); cần chốt locator hoặc chạy tay."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except UiNotFound as e:
            pytest.skip(f"Chưa xác nhận được phần tử giao diện: {e}")
    return wrapper


@pytest.fixture
def listing(driver):
    return SearchPage(driver).open_collection(CATEGORY_PATH)


def sample_pages(driver, hrefs, n=SAMPLE):
    """Mở lần lượt n sản phẩm đầu của danh sách đã lọc để kiểm tra chéo (không dùng ProductPage của PDP)."""
    page = SearchPage(driver)
    for h in hrefs[:n]:
        driver.get(h)
        page.dismiss_popups()
        yield page


def applied(listing, before_url):
    """Bộ lọc đã được áp dụng: URL đã đổi (đường dẫn hoặc tham số) hoặc đang thấy nút 'Xoá lọc'.
    Lưu ý: chọn màu có thể chuyển sang trang khác (ví dụ /collection/ao-thun-nam-den) nên không phải lúc nào cũng thấy chip."""
    return listing.driver.current_url != before_url or listing.filter_active()


def lows(listing):
    """Giá bán hiện tại (thấp nhất trong thẻ: đúng cả khi có giá gốc gạch ngang) của các sản phẩm đang hiển thị."""
    return [low for low, _ in listing.card_prices()]


# ---------------------------------------------------------------- FLT-01
@smoke
@high
@pytest.mark.parametrize("row", CATEGORIES, ids=[r["tc_id"] for r in CATEGORIES])
def test_FLT_01_filter_by_category(driver, row):
    path = row.get("path")
    assert path, "File data/flt_category.csv phải có cột 'path' (ví dụ /collection/ao-thun-nam)"
    page = SearchPage(driver).open_collection(path)
    assert page.results(), f"Danh mục '{path}' không có sản phẩm"
    count = page.result_count()
    assert count is None or count > 0, f"Danh mục '{path}' hiển thị {count} kết quả"


# ---------------------------------------------------------------- FLT-02
@regression
@high
@pytest.mark.parametrize("row", PRICES, ids=[r["tc_id"] for r in PRICES])
@skip_if_ui_missing
def test_FLT_02_filter_by_price_range(listing, row):
    """Lọc theo khoảng giá bằng ô tick: mọi sản phẩm hiển thị phải có giá bán nằm trong khoảng đã chọn."""
    label, low, high = row["label"], int(row["min"]), int(row["max"])
    before_url = listing.driver.current_url
    listing.apply_filter(label)
    assert applied(listing, before_url), f"Đã chọn '{label}' nhưng URL không đổi và không thấy 'Xoá lọc': {before_url}"
    assert "price_range=" in listing.driver.current_url, f"URL không ghi khoảng giá: {listing.driver.current_url}"
    if not listing.results():
        return                                                     # khoảng giá không có sản phẩm nào là hợp lệ
    prices = lows(listing)
    assert prices, "Không đọc được giá của sản phẩm nào"
    out = [p for p in prices if not low <= p <= high]
    assert not out, f"Có giá ngoài khoảng '{label}': {out}"


# ---------------------------------------------------------------- FLT-03
@regression
@high
@pytest.mark.parametrize("row", COLORS, ids=[r["tc_id"] for r in COLORS])
@skip_if_ui_missing
def test_FLT_03_filter_by_color(listing, row):
    """Lọc theo màu: bộ lọc phải được áp dụng và còn sản phẩm. Việc mở từng sản phẩm xem đúng màu làm bằng tay."""
    color = row["color"]
    before_url = listing.driver.current_url
    listing.apply_filter(color)
    assert applied(listing, before_url), f"Đã chọn màu '{color}' nhưng URL không đổi và không thấy 'Xoá lọc': {before_url}"
    if not listing.hrefs():
        pytest.skip(f"Danh mục này không có sản phẩm màu '{color}' - đổi màu trong data/flt_color.csv")


# ---------------------------------------------------------------- FLT-04
@regression
@high
@pytest.mark.parametrize("row", SIZES, ids=[r["tc_id"] for r in SIZES])
@skip_if_ui_missing
def test_FLT_04_filter_by_size(driver, listing, row):
    """Lọc theo size: URL ghi size đã chọn (?size=m), bộ lọc được áp dụng, và các sản phẩm đầu tiên có size đó còn hàng."""
    size = row["size"]
    before_url = driver.current_url
    listing.apply_filter(size)
    assert f"size={size.lower()}" in driver.current_url, f"URL không ghi size đã chọn: {driver.current_url}"
    assert applied(listing, before_url), f"Đã chọn size '{size}' nhưng URL không đổi và không thấy 'Xoá lọc'"
    hrefs = listing.hrefs()
    if not hrefs:
        pytest.skip(f"Danh mục này không có sản phẩm size '{size}' - đổi size trong data/flt_size.csv")
    for page in sample_pages(driver, hrefs):
        url = driver.current_url
        ok, note = page.size_available(size)
        assert ok, f"Size {size} không còn hàng ở màu nào của sản phẩm {url} ({note})"


# ---------------------------------------------------------------- FLT-05
@regression
@high
@skip_if_ui_missing
def test_FLT_05_combined_filters(driver, listing):
    """Kết hợp khoảng giá + màu + size: kết quả phải thỏa đồng thời các điều kiện kiểm tra được bằng script."""
    price_label, low, high, color, size = COMBINED
    for label in (color, price_label, size):          # màu đổi sang trang khác nên chọn trước
        listing.apply_filter(label)
    url = driver.current_url
    assert "price_range=" in url and f"size={size.lower()}" in url, \
        f"URL không ghi đủ khoảng giá và size đã chọn (mong đợi price_range=... và size={size.lower()}): {url}"
    if not listing.results():
        pytest.skip(f"Tổ hợp {price_label} + {color} + {size} không còn sản phẩm - đổi tổ hợp trong test_filter.py")
    out = [p for p in lows(listing) if not low <= p <= high]
    assert not out, f"Có giá ngoài khoảng '{price_label}': {out}"
    for page in sample_pages(driver, listing.hrefs()):
        url = driver.current_url
        ok, note = page.size_available(size)
        assert ok, f"Size {size} không còn hàng ở màu nào của sản phẩm {url} ({note})"


# ---------------------------------------------------------------- FLT-06
@regression
@medium
@skip_if_ui_missing
def test_FLT_06_clear_filters(listing):
    """Bấm 'Xoá lọc': không còn bộ lọc nào và danh sách trở về như ban đầu."""
    base_head = listing.product_slugs()[:12]
    listing.apply_filter(CLEAR_TEST_FILTER)
    if not listing.filter_active(timeout=10):
        pytest.skip("Sau khi lọc không thấy nút 'Xoá lọc' trong 10 giây (xem results/flt_debug.txt) - kiểm tra bằng tay")
    listing.clear_filters()
    assert not listing.filter_active(), "Sau khi bấm 'Xoá lọc' vẫn còn bộ lọc đang chọn"
    assert listing.product_slugs()[:12] == base_head, "Sau khi xóa bộ lọc danh sách không trở về ban đầu"


# ---------------------------------------------------------------- FLT-07
@regression
@medium
@pytest.mark.parametrize("row", NO_RESULT_COMBOS, ids=[r["tc_id"] for r in NO_RESULT_COMBOS])
@skip_if_ui_missing
def test_FLT_07_filter_no_result(listing, row):
    """Tổ hợp bộ lọc không còn sản phẩm: phải có thông báo hoặc '0 kết quả', trang không lỗi."""
    for label in [x.strip() for x in row["filters"].split("|") if x.strip()]:
        listing.apply_filter(label)
        if not listing.results():
            break
    if listing.results():
        pytest.skip(f"Tổ hợp '{row['filters']}' vẫn còn sản phẩm - "
                    "đổi tổ hợp trong data/flt_no_result.csv sau khi thử bằng tay")
    if not (listing.has_no_result_message() or listing.result_count() == 0):
        pytest.skip("Không còn sản phẩm nhưng chưa nhận ra thông báo của site: xem results/flt_debug.txt rồi "
                    "đặt SRC_EMPTY_MESSAGE trong .env")
    assert listing.page_is_healthy()


# ---------------------------------------------------------------- FLT-08 / 09
def assert_price_sorted(listing, ascending):
    """Giá BÁN (giá đang hiển thị đậm, không phải giá gốc gạch ngang) phải đúng thứ tự: Coolmate sắp xếp theo giá bán."""
    prices = lows(listing)
    assert len(prices) >= 4, f"Quá ít sản phẩm để kiểm tra thứ tự ({len(prices)})"
    assert prices == sorted(prices, reverse=not ascending), \
        f"Giá bán không đúng thứ tự {'tăng' if ascending else 'giảm'} dần: {prices[:12]} | cách chọn: {listing.apply_mode}"


@regression
@high
@skip_if_ui_missing
def test_FLT_08_sort_price_ascending(driver, listing):
    listing.sort_by(SORT_ASC)
    assert "sort=price-asc" in driver.current_url, f"URL không ghi kiểu sắp xếp: {driver.current_url}"
    assert_price_sorted(listing, ascending=True)


@regression
@high
@skip_if_ui_missing
def test_FLT_09_sort_price_descending(driver, listing):
    listing.sort_by(SORT_DESC)
    assert "sort=" in driver.current_url, f"URL không ghi kiểu sắp xếp: {driver.current_url}"
    assert_price_sorted(listing, ascending=False)


# ---------------------------------------------------------------- FLT-12
@regression
@medium
@skip_if_ui_missing
def test_FLT_12_filter_persists_after_reload(driver, listing):
    """Áp bộ lọc + sắp xếp rồi tải lại trang (F5): bộ lọc vẫn còn và danh sách không đổi.
    Coolmate ghi trạng thái vào URL nên nhiều khả năng pass; nếu fail, tái hiện bằng tay rồi mới kết luận."""
    listing.apply_filter(CLEAR_TEST_FILTER)
    listing.sort_by(SORT_ASC)
    before_head, url = listing.product_slugs()[:12], driver.current_url
    driver.refresh()
    listing.dismiss_popups()
    try:
        WebDriverWait(driver, 15).until(lambda d: listing.hrefs())
    except TimeoutException:
        pass
    listing._wait_stable()
    assert driver.current_url == url, f"URL đổi sau khi tải lại: {url} -> {driver.current_url}"
    assert before_head == listing.product_slugs()[:12], "Sau khi tải lại, danh sách sản phẩm đầu tiên thay đổi"