"""Test module Giao diện và tương thích (UI) - phụ trách: TV3 (Lâm).
Chỉ có script cho UI-01, UI-02, UI-06. UI-03, 04, 05, 07 là loại M - chạy tay.
Tên hàm bắt buộc dạng test_UI_xx_... để conftest.py lấy đúng TC ID.
"""
import pytest

from pages.home_page import HomePage
from utils import config
from utils.test_data import read_csv

# ---- Dữ liệu kiểm thử (Data-driven) đọc từ thư mục data/
VIEWPORTS = read_csv("ui_viewports.csv")

from tests import browser_session

driver = browser_session.driver      # dùng chung một Chrome cho cả file (nhanh hơn)

smoke = pytest.mark.smoke
regression = pytest.mark.regression
high = pytest.mark.high
medium = pytest.mark.medium
low = pytest.mark.low


@pytest.fixture
def home(driver):
    page = HomePage(driver).load()
    yield page
    page.reset_viewport()


# ---------------------------------------------------------------- UI-01
@smoke
@high
def test_UI_01_open_home_page(home):
    """UI-01: Trang chủ đầy đủ, tiêu đề đúng, không lỗi console nghiêm trọng (cũng là smoke test của khung)."""
    host = config.BASE_URL.split("//")[-1].split("/")[0]
    assert host in home.driver.current_url, f"Không ở trang Coolmate: {home.driver.current_url}"
    assert "coolmate" in home.title().lower(), f"Tiêu đề trang không đúng: {home.title()!r}"
    assert home.has_header(), "Không thấy header"
    assert home.has_footer(), "Không thấy footer"
    assert home.product_link_count() > 0, "Trang chủ không hiển thị sản phẩm nào"
    errors = home.console_errors()
    if errors is not None:
        serious = [e for e in errors if "Uncaught" in e]
        assert not serious, f"Có {len(serious)} lỗi JavaScript chưa bắt trong console: {serious[:2]}"


# ---------------------------------------------------------------- UI-02
@regression
@medium
@pytest.mark.parametrize("row", VIEWPORTS, ids=[r["tc_id"] for r in VIEWPORTS])
def test_UI_02_responsive_layout(home, row):
    """UI-02: Đổi cỡ cửa sổ; bố cục tự điều chỉnh và không tràn ngang. Mỗi cỡ được chụp ảnh vào evidence/auto/.
    Việc 'nút không bị che' cần xem lại bằng mắt trên ảnh chụp."""
    w, h = int(row["width"]), int(row["height"])
    home.resize_and_reload(w, h)
    home.take_screenshot(f"UI-02_{w}x{h}", sub="auto")
    scroll_w, inner_w = home.widths()
    assert home.has_header(), f"Không thấy header ở cỡ {w}x{h}"
    assert home.product_link_count() > 0, f"Không có sản phẩm nào ở cỡ {w}x{h}"
    assert scroll_w <= inner_w + 2, f"Trang bị tràn ngang ở cỡ {w}x{h}: nội dung {scroll_w}px > khung {inner_w}px"


# ---------------------------------------------------------------- UI-06
@regression
@low
def test_UI_06_header_footer_links(home):
    """UI-06: Mọi link header/footer cùng tên miền không được trả 404/410/5xx. Danh sách ghi ở results/ui_links.csv."""
    links = home.internal_links()
    assert links, "Không lấy được link nào ở header/footer - kiểm tra NAV_LINK_CSS"
    statuses = home.link_statuses(links)
    home.save_link_report(statuses)
    broken = [(u, s) for u, s in statuses if s in (404, 410) or s >= 500]
    assert not broken, f"Có {len(broken)}/{len(statuses)} link lỗi: {broken[:5]}"