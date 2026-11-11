"""Page Object: HomePage - phụ trách: TV3 - module: UI.
Quy tắc: locator đặt ở đầu lớp; method là hành động nghiệp vụ; KHÔNG assert trong page.
"""
import csv
from pathlib import Path
from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

JS_WIDTHS = "return [document.documentElement.scrollWidth, window.innerWidth];"

JS_LINKS = """
const out = new Set();
document.querySelectorAll(arguments[0]).forEach(a => {
  const h = a.href || '';
  if (/^https?:/i.test(h)) out.add(h.split('#')[0]);
});
return [...out];
"""

# Gọi từng link bằng fetch ngay trong trang (cùng nguồn, cùng cookie) để lấy mã trạng thái thật,
# tránh bị chặn như khi gọi bằng thư viện requests bên ngoài.
JS_STATUS = """
const urls = arguments[0];
const done = arguments[arguments.length - 1];
(async () => {
  const out = [];
  for (const u of urls) {
    try {
      const r = await fetch(u, {method: 'GET', credentials: 'same-origin', redirect: 'follow'});
      out.push([u, r.status]);
    } catch (e) { out.push([u, 0]); }
  }
  done(out);
})();
"""


class HomePage(BasePage):
    PATH = "/"

    HEADER = (By.CSS_SELECTOR, "header")
    FOOTER = (By.CSS_SELECTOR, "footer")
    PRODUCT_LINK = (By.CSS_SELECTOR, "a[href*='/product/']")
    NAV_LINK_CSS = "header a[href], footer a[href]"     # link ở header + footer (TODO: xác nhận bằng check_locators.py)

    def load(self):
        self.open(self.PATH)
        self.dismiss_popups()
        return self

    def title(self):
        return self.driver.title

    # ================= UI-01 =================
    def has_header(self):
        return any(e.is_displayed() for e in self.driver.find_elements(*self.HEADER))

    def has_footer(self):
        return bool(self.driver.find_elements(*self.FOOTER))

    def product_link_count(self):
        return len(self.driver.find_elements(*self.PRODUCT_LINK))

    def console_errors(self):
        """Danh sách thông báo mức SEVERE trong console trình duyệt; None nếu driver không hỗ trợ đọc log."""
        try:
            return [e["message"] for e in self.driver.get_log("browser") if e.get("level") == "SEVERE"]
        except Exception:
            return None

    # ================= UI-02 =================
    def set_viewport(self, width, height):
        """Đặt kích thước vùng hiển thị (Chrome DevTools). Cửa sổ Chrome thật không thu nhỏ dưới ~500px nên
        phải dùng giả lập thiết bị để có được cỡ 375x812."""
        mobile = width <= 768
        try:
            self.driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                "width": width, "height": height, "deviceScaleFactor": 1, "mobile": mobile})
        except Exception:
            self.driver.set_window_size(width, height)       # dự phòng cho trình duyệt không có CDP
        return self

    def reset_viewport(self):
        try:
            self.driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
        except Exception:
            pass
        return self

    def resize_and_reload(self, width, height):
        self.set_viewport(width, height)
        self.driver.refresh()
        try:
            WebDriverWait(self.driver, 15).until(lambda d: self.has_header())
        except TimeoutException:
            pass
        self.dismiss_popups()
        return self

    def widths(self):
        """(độ rộng nội dung, độ rộng khung nhìn): nội dung > khung nhìn nghĩa là bị tràn ngang."""
        scroll_w, inner_w = self.driver.execute_script(JS_WIDTHS)
        return scroll_w, inner_w

    # ================= UI-06 =================
    def internal_links(self, limit=60):
        """Link header/footer cùng tên miền với trang hiện tại (không trùng lặp, tối đa `limit`)."""
        host = urlparse(self.driver.current_url).netloc
        links = self.driver.execute_script(JS_LINKS, self.NAV_LINK_CSS)
        same = [u for u in links if urlparse(u).netloc == host]
        return same[:limit]

    def link_statuses(self, urls):
        """Danh sách (url, mã trạng thái); mã 0 nghĩa là không gọi được."""
        self.driver.set_script_timeout(120)
        return self.driver.execute_async_script(JS_STATUS, urls)

    @staticmethod
    def save_link_report(rows, name="ui_links.csv"):
        RESULTS_DIR.mkdir(exist_ok=True)
        path = RESULTS_DIR / name
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["url", "status"])
            w.writerows(rows)
        return path