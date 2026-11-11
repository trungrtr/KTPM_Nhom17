"""Page Object: SearchPage - phụ trách: TV3 - module: SRC, FLT.
Quy tắc: locator đặt ở đầu lớp; method là hành động nghiệp vụ; KHÔNG assert trong page.
"""
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlunparse
from urllib.parse import urlparse

from selenium.common.exceptions import (ElementClickInterceptedException,
                                        ElementNotInteractableException,
                                        StaleElementReferenceException, TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"

PRICE_RE = re.compile(r"(\d{1,3}(?:[.,]\d{3})+)\s*(?:đ|₫|VNĐ|VND)", re.I)
SIZE_LABELS = ["XS", "S", "M", "L", "XL", "2XL", "XXL", "3XL", "4XL"]
# Bản nhẹ của JS_COLLECT_CARDS: chỉ lấy danh sách href (dùng khi chờ kết quả, gọi liên tục)
JS_ROOT = """
const sel = arguments[0], scoped = arguments[1];
let root = document;
if (scoped) {      // trang danh mục: chỉ lấy khung danh sách chính (div.grid ... md:grid-cols-4), bỏ khối sản phẩm nổi bật bên trên
  let best = null, bestN = 0;
  document.querySelectorAll('div.grid[class*="md:grid-cols-4"]').forEach(g => {
    const n = g.querySelectorAll(sel).length; if (n > bestN) { best = g; bestN = n; }
  });
  if (best) root = best; else return [];
}
"""

JS_QUICK_HREFS = JS_ROOT + """
const seen = new Set();
root.querySelectorAll(sel).forEach(a => {
  const h = (a.href || '').split('#')[0]; if (h) seen.add(h);
});
return [...seen];
"""

# Dòng "79 kết quả" ở đầu danh sách sản phẩm
JS_RESULT_COUNT = """
const m = (document.body.innerText || '').match(/(\\d[\\d.]*)\\s*kết quả/i);
return m ? parseInt(m[1].replace(/\\./g, ''), 10) : null;
"""

SORT_LABELS = ["Mặc định", "Bán chạy", "Mới nhất", "Giá thấp đến cao", "Giá cao đến thấp", "%Giảm giá nhiều"]
# Tham số ?sort=... trên URL: price-asc (ảnh chụp site) và price-desc (nhật ký: ô sắp xếp hiện 'Giá cao đến thấp') đều đã xác nhận
SORT_PARAMS = {"Giá thấp đến cao": "price-asc", "Giá cao đến thấp": "price-desc"}

JS_COMBOBOXES = """
return [...document.querySelectorAll('[role=combobox]')].map(e => ((e.textContent || '').trim().slice(0, 30) +
  ' | hiển thị: ' + !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length) + ' | mở: ' + e.getAttribute('aria-expanded')))
  .concat(['số mục role=option đang có trong trang: ' + document.querySelectorAll('[role=option]').length]);
"""

JS_MAIN_TEXT = """
const m = document.querySelector('main') || document.body;
return (m.innerText || '').replace(/\\s+/g, ' ').slice(0, 500);
"""

# Size hết hàng trên trang sản phẩm: nút không bấm được. So khớp đúng TỪNG TỪ trong class, vì class kiểu
# 'disabled:cursor-not-allowed' của Tailwind chỉ áp dụng khi nút bị disabled chứ không có nghĩa là nút đang bị disabled.
SOLD_OUT_TOKENS = {"pointer-events-none", "cursor-not-allowed", "line-through"}

# Chỉ lấy nút size CHÍNH (class có min-w-13 và rounded-xl), không lấy nút 'thêm nhanh' của các sản phẩm gợi ý
JS_PDP_SIZES = r"""
const out = [];
document.querySelectorAll('button').forEach(b => {
  const c = String(b.className);
  if (!/(^|\s)min-w-13(\s|$)/.test(c) || !/(^|\s)rounded-xl(\s|$)/.test(c)) return;
  const r = b.getBoundingClientRect();
  out.push({text: (b.textContent || '').replace(/[\u00a0\s]+/g, ' ').trim(), cls: c,
            disabled: !!b.disabled || b.getAttribute('aria-disabled') === 'true', shown: r.width > 0 && r.height > 0});
});
return out;
"""

# Các màu của chính sản phẩm đang xem (liên kết cùng đường dẫn có ?color=...)
JS_PRODUCT_COLORS = r"""
const colors = new Set();
document.querySelectorAll('a[href*="color="]').forEach(a => {
  try { const u = new URL(a.href); if (u.pathname === location.pathname) colors.add(u.searchParams.get('color')); } catch (e) {}
});
return [...colors];
"""

NO_RESULT_PHRASES = ["không tìm thấy", "không có sản phẩm", "không có kết quả", "0 sản phẩm"]
ERROR_PHRASES = ["internal server error", "application error", "500 error", "502 bad gateway", "503 service"]

JS_SET_VALUE = """
const el = arguments[0], v = arguments[1];
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(el, v);
el.dispatchEvent(new Event('input', {bubbles: true}));
el.dispatchEvent(new Event('change', {bubbles: true}));
"""

# Ô nhập có thật sự nhìn thấy và không bị che không (Selenium báo "displayed" chưa đủ để gõ được)
JS_INTERACTABLE = """
const el = arguments[0];
const r = el.getBoundingClientRect();
if (r.width < 2 || r.height < 2) return false;
const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
return !!e && (e === el || el.contains(e) || e.contains(el));
"""

# Dự phòng khi ô không gõ được bằng send_keys: phát phím Enter và gửi form bằng JavaScript
JS_PRESS_ENTER = """
const el = arguments[0];
el.focus();
for (const t of ['keydown', 'keypress', 'keyup'])
  el.dispatchEvent(new KeyboardEvent(t, {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
const f = el.closest('form');
if (f) { if (f.requestSubmit) f.requestSubmit(); else f.submit(); }
"""

# Gom mỗi sản phẩm (dedupe theo href); leo lên tối đa 6 cấp cho tới khi thấy giá.
JS_COLLECT_CARDS = JS_ROOT + """
const re = /\\d{1,3}(?:[.,]\\d{3})+\\s*(?:đ|₫|VNĐ|VND)/i;
const seen = new Set(), out = [];
root.querySelectorAll(sel).forEach(a => {
  const href = (a.href || '').split('#')[0]; if (!href || seen.has(href)) return; seen.add(href);
  let node = a;
  for (let i = 0; i < 6 && node.parentElement && !re.test(node.innerText || ''); i++) node = node.parentElement;
  const img = node.querySelector('img');
  out.push({href: href, text: (node.innerText || '').trim(),
            image: img ? (img.currentSrc || img.src || '') : ''});
});
return out;
"""


# Phát đủ chuỗi sự kiện chuột như người dùng (Radix Select chỉ mở khi nhận pointerdown, el.click() không đủ)
JS_FULL_CLICK = """
for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
  const E = t.startsWith('pointer') ? PointerEvent : MouseEvent;
  arguments[0].dispatchEvent(new E(t, {bubbles: true, cancelable: true, button: 0, pointerType: 'mouse', view: window}));
}
"""

# Liên kết có tham số URL bằng giá trị cho trước, ví dụ ?size=s
JS_PARAM_LINKS = """
const key = arguments[0], val = arguments[1].toLowerCase();
return [...document.querySelectorAll('a[href*="' + key + '="]')].filter(a => {
  try { return (new URL(a.href).searchParams.get(key) || '').toLowerCase() === val; } catch (e) { return false; }
});
"""


class UiNotFound(RuntimeError):
    """Không tìm thấy phần tử giao diện mong đợi (thường do locator chưa khớp site), không phải lỗi của website."""


class SearchPage(BasePage):
    PATH = ""  # trang chủ: ô tìm kiếm nằm trên header. TODO: xác nhận trên site thật

    # ---- locator (mỗi locator gộp nhiều ứng viên bằng dấu phẩy / "|"; TODO: xác nhận bằng check_locators.py)
    SEARCH_ICON = (By.CSS_SELECTOR,
                   "[aria-label*='tìm kiếm' i], [aria-label*='search' i], header a[href*='search']")
    SEARCH_INPUT = (By.CSS_SELECTOR,
                    "input[type='search'], input[placeholder*='Tìm' i], input[name='q'], input[name='keyword']")
    PRODUCT_CARD = (By.CSS_SELECTOR, "a[href*='/product/']")
    # Bộ lọc của Coolmate là các LIÊN KẾT thường, đã đo trên trang thật:
    #   size : <a href="/collection/ao-thun-nam?size=s">          màu : <a href="/collection/ao-thun-nam-den" aria-label="Filter by color Đen">
    #   giá  : <a href="...?price_range=200000-300000" aria-label="Filter by 200.000đ - 300.000đ">
    FILTER_ANCHOR = "//a[@aria-label='Filter by {t}' or @aria-label='Filter by color {t}']"
    SORT_TRIGGER = (By.XPATH, "//button[@role='combobox'][" + " or ".join(
        f"normalize-space(.)='{x}'" for x in SORT_LABELS) + "]")                  # ô "Sắp xếp theo" (Radix Select), chọn theo chữ đang hiển thị
    SORT_OPTION = "//*[@role='option'][normalize-space(.)='{t}']"           # mục trong danh sách thả xuống
    # Nút "Xoá lọc" (cạnh các chip đang chọn như "M ✕"); chỉ xuất hiện khi đang có bộ lọc
    CLEAR_FILTER = (By.XPATH,
                    "//*[(self::button or self::a or not(*))][contains(normalize-space(.), 'Xoá lọc')"
                    " or contains(normalize-space(.), 'Xóa lọc') or contains(normalize-space(.), 'Xoá bộ lọc')"
                    " or contains(normalize-space(.), 'Xóa bộ lọc') or contains(normalize-space(.), 'Xóa tất cả')"
                    " or contains(normalize-space(.), 'Xoá tất cả') or contains(normalize-space(.), 'Bỏ lọc')]")

    def __init__(self, driver):
        super().__init__(driver)
        self._prev_url = ""
        self.last_change_time = 0.0
        self.scope_grid = False          # True sau open_collection: chỉ đọc khung danh sách chính
        self.last_href = ""              # liên kết lọc vừa dùng
        self.apply_mode = ""             # bấm hay mở thẳng liên kết (ghi vào nhật ký chẩn đoán)

    def load(self):
        self.open(self.PATH)
        self.dismiss_popups()
        return self

    # ================= hàm hỗ trợ nội bộ =================
    def _try(self, locator, timeout=2):
        """Phần tử HIỂN THỊ đầu tiên khớp locator, hoặc None nếu không có."""
        def shown(d):
            for el in d.find_elements(*locator):
                if el.is_displayed():
                    return el
            return False
        try:
            return WebDriverWait(self.driver, timeout).until(shown)
        except TimeoutException:
            return None

    def js_click(self, el):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        self.driver.execute_script("arguments[0].click();", el)

    def _body_text(self):
        return self.driver.execute_script("return document.body.innerText || '';").lower()

    # ================= SRC =================
    def _interactable(self, el):
        try:
            return el.is_displayed() and el.is_enabled() and self.driver.execute_script(JS_INTERACTABLE, el)
        except Exception:
            return False

    def _wait_input(self, timeout):
        """Ô tìm kiếm đã nhập được (nhìn thấy, đủ lớn, không bị che), hoặc None."""
        def ready(d):
            for el in d.find_elements(*self.SEARCH_INPUT):
                if self._interactable(el):
                    return el
            return False
        try:
            return WebDriverWait(self.driver, timeout).until(ready)
        except TimeoutException:
            return None

    def open_search_box(self):
        box = self._wait_input(1)
        if box is None:                                    # thanh tìm kiếm đang thu gọn -> bấm biểu tượng
            icon = self._try(self.SEARCH_ICON)
            if icon is not None:
                self.js_click(icon)
            box = self._wait_input(5)
        if box is None:                                    # dự phòng: lấy ô đầu tiên có trong DOM
            els = self.driver.find_elements(*self.SEARCH_INPUT)
            if els:
                return els[0]
            raise UiNotFound("Không tìm thấy ô tìm kiếm - kiểm tra SEARCH_ICON / SEARCH_INPUT")
        return box

    def _search_via_js(self, box, keyword):
        self.driver.execute_script(JS_SET_VALUE, box, keyword)
        self.driver.execute_script(JS_PRESS_ENTER, box)

    def search(self, keyword):
        box = self.open_search_box()
        self._prev_url = self.driver.current_url
        if any(ord(c) > 0xFFFF for c in keyword) or not self._interactable(box):
            self._search_via_js(box, keyword)              # emoji, hoặc ô không gõ được trực tiếp
            return self
        try:
            box.send_keys(Keys.CONTROL, "a", Keys.DELETE)
            box.send_keys(keyword)
            box.send_keys(Keys.ENTER)
        except (ElementNotInteractableException, ElementClickInterceptedException):
            self._search_via_js(box, keyword)
        return self

    def has_no_result_message(self):
        text = self._body_text()
        phrases = list(NO_RESULT_PHRASES)
        extra = os.getenv("SRC_EMPTY_MESSAGE", "").strip().lower()      # câu thông báo thật của Coolmate (đặt trong .env)
        if extra:
            phrases.append(extra)
        return any(p in text for p in phrases)

    def _signature(self):
        """Dấu hiệu trạng thái kết quả hiện tại: tuple href, ("NO_RESULT",) hoặc None nếu chưa có gì."""
        if self.driver.current_url == self._prev_url:
            return None
        hrefs = self.hrefs()
        if hrefs:
            return tuple(hrefs)
        return ("NO_RESULT",) if self.has_no_result_message() else None

    def wait_results(self, timeout=15, stable_for=3.0):
        """Chờ kết quả tìm kiếm ĐÃ ỔN ĐỊNH (không đổi trong `stable_for` giây) sau khi URL đã đổi.
        Trang tìm kiếm hiện danh sách gợi ý trước rồi mới thay bằng kết quả thật, nên không được dừng ở lần
        thấy sản phẩm đầu tiên. self.last_change_time ghi thời điểm danh sách đổi lần cuối (dùng đo thời gian)."""
        state = {"sig": None, "t": time.perf_counter()}

        def stable(d):
            sig, now = self._signature(), time.perf_counter()
            if sig != state["sig"]:
                state["sig"], state["t"] = sig, now
            return sig is not None and now - state["t"] >= stable_for

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(stable)
            self.last_change_time = state["t"]
            return True
        except TimeoutException:
            self.last_change_time = state["t"]
            return False

    def results(self):
        """Danh sách dict {href, text, image} của các sản phẩm đang hiển thị."""
        return self.driver.execute_script(JS_COLLECT_CARDS, self.PRODUCT_CARD[1], self.scope_grid)

    def hrefs(self):
        """Danh sách href sản phẩm (không trùng, bỏ #fragment). Nhẹ, dùng được khi chờ."""
        return self.driver.execute_script(JS_QUICK_HREFS, self.PRODUCT_CARD[1], self.scope_grid)

    def product_slugs(self):
        """Danh sách đường dẫn sản phẩm không trùng, bỏ ?color=... và #...: dùng để so sánh hai danh sách kết quả."""
        out = []
        for h in self.hrefs():
            path = urlparse(h).path
            if path not in out:
                out.append(path)
        return out

    @staticmethod
    def prices_in(text):
        return [int(re.sub(r"[.,]", "", m)) for m in PRICE_RE.findall(text)]

    def current_prices(self):
        """Giá hiện tại (thấp nhất trong thẻ - đúng cả khi có giá gốc + giá sale)."""
        out = []
        for r in self.results():
            p = self.prices_in(r["text"])
            if p:
                out.append(min(p))
        return out

    def page_is_healthy(self):
        text = self._body_text()
        return bool(self.driver.title.strip()) and not any(p in text for p in ERROR_PHRASES)

    def timed_search(self, keyword):
        self.load()
        t0 = time.perf_counter()
        self.search(keyword)
        self.wait_results()
        return max(self.last_change_time - t0, 0.0)

    # ================= FLT =================
    def result_count(self):
        """Số trong dòng 'N kết quả' ở đầu danh sách (ví dụ '79 kết quả'); None nếu trang không hiển thị."""
        return self.driver.execute_script(JS_RESULT_COUNT)

    def open_collection(self, path):
        """Vào thẳng trang danh mục theo đường dẫn, ví dụ /collection/ao-thun-nam, và chờ có sản phẩm + số kết quả.
        Từ đây results()/hrefs() chỉ đọc khung danh sách chính (bỏ khối sản phẩm nổi bật 200.000đ ở phía trên)."""
        self.scope_grid = True
        self.open(path)
        self.dismiss_popups()
        try:
            WebDriverWait(self.driver, 15).until(lambda d: self.hrefs() and self.result_count() is not None)
        except TimeoutException:
            pass
        self._wait_stable()
        return self

    @staticmethod
    def _shown(el):
        try:
            return el.is_displayed()
        except StaleElementReferenceException:
            return False

    def _native_click(self, el):
        """Bấm như người dùng: cuộn tới rồi bấm thật bằng Selenium; không được thì ActionChains; cuối cùng phát đủ chuỗi
        sự kiện chuột bằng JavaScript (el.click() của JavaScript không đủ để mở ô Radix Select)."""
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
            return "bấm thật"
        except (ElementClickInterceptedException, ElementNotInteractableException):
            pass
        try:
            ActionChains(self.driver).move_to_element(el).click().perform()
            return "ActionChains"
        except Exception:
            pass
        self.driver.execute_script(JS_FULL_CLICK, el)
        return "JavaScript đủ chuỗi sự kiện"

    def _wait_url_change(self, before_url, timeout=6):
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(lambda d: d.current_url != before_url)
            return True
        except TimeoutException:
            return False

    def _wait_stable(self, stable_for=2.0, timeout=12):
        """Chờ danh sách sản phẩm đứng yên sau khi lọc/sắp xếp (URL đổi ngay nhưng danh sách tải sau)."""
        state = {"sig": None, "t": time.perf_counter()}

        def stable(d):
            sig, now = tuple(self.hrefs()), time.perf_counter()
            if sig != state["sig"]:
                state["sig"], state["t"] = sig, now
            return now - state["t"] >= stable_for
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.3).until(stable)
        except TimeoutException:
            pass

    def snapshot(self, tag, shot=False):
        """Ghi trạng thái trang vào results/flt_debug.txt (và chụp ảnh nếu shot=True) để chẩn đoán. Không bao giờ làm test lỗi."""
        try:
            cards = self.results()
            lines = [f"[{datetime.now():%H:%M:%S}] {tag}",
                     f"  url                 : {self.driver.current_url}",
                     f"  cách áp dụng        : {self.apply_mode or '-'}",
                     f"  liên kết lọc đã dùng: {self.last_href or '-'}",
                     f"  nút 'Xoá lọc'       : {'CÓ' if any(self._shown(e) for e in self.driver.find_elements(*self.CLEAR_FILTER)) else 'không'}",
                     f"  dòng 'N kết quả'    : {self.result_count()}",
                     f"  số sản phẩm (khung chính): {len(cards)}, trong đó thẻ có color=... : {sum('color=' in c['href'] for c in cards)}"]
            try:
                lines.append("  ô combobox          : " + " ; ".join(self.driver.execute_script(JS_COMBOBOXES)))
            except Exception:
                pass
            for c in cards[:5]:
                lines.append("   - " + " | ".join(c["text"].split("\n")[:3])[:90] + f" | giá đọc được: {self.prices_in(c['text'])}")
            if cards:
                lines.append("  giá bán 12 sản phẩm đầu: " + str([min(self.prices_in(c["text"]) or [0]) for c in cards[:12]]))
            else:
                lines.append("  (không có sản phẩm) nội dung phần chính của trang: " + self.driver.execute_script(JS_MAIN_TEXT))
            RESULTS_DIR.mkdir(exist_ok=True)
            with open(RESULTS_DIR / "flt_debug.txt", "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n\n")
            if shot:
                self.take_screenshot("FLTDBG_" + re.sub(r"\W+", "_", tag)[:40], sub="auto")
        except Exception:
            pass

    def _filter_anchor(self, label):
        """Liên kết lọc theo nhãn hiển thị. Size: liên kết có ?size=<nhãn>; màu và khoảng giá: liên kết có aria-label 'Filter by ...'."""
        if label in SIZE_LABELS:
            els = self.driver.execute_script(JS_PARAM_LINKS, "size", label.lower())
            els = [e for e in els if "/collection/" in (e.get_attribute("href") or "")] or els
        else:
            els = self.driver.find_elements(By.XPATH, self.FILTER_ANCHOR.format(t=label))
        return els[0] if els else None

    def apply_filter(self, label):
        """Áp dụng một bộ lọc. Bộ lọc của Coolmate là liên kết thường: nếu liên kết đang hiện thì bấm như người dùng;
        nếu nhóm đang thu gọn (liên kết ẩn) hoặc bấm không có tác dụng thì mở thẳng địa chỉ của liên kết đó."""
        a = self._filter_anchor(label)
        if a is None:
            self.snapshot(f"KHONG THAY lien ket loc '{label}'", shot=True)
            raise UiNotFound(f"Không thấy liên kết lọc '{label}'")
        href = a.get_attribute("href")
        before_u = self.driver.current_url
        self.last_href, self.apply_mode = href, "mở thẳng liên kết (liên kết đang ẩn trong nhóm thu gọn)"
        if self._shown(a):
            how = self._native_click(a)
            if self._wait_url_change(before_u, 6):
                self.apply_mode = f"bấm ({how})"
            else:
                self.apply_mode = f"bấm ({how}) KHÔNG có tác dụng -> mở thẳng liên kết"
        if self.driver.current_url == before_u:
            self.driver.get(href)
        self.dismiss_popups()
        self._wait_stable()
        self.snapshot(f"Đã chọn '{label}'")
        return self

    def filter_active(self, timeout=3):
        """Đang có bộ lọc nào được áp dụng không (thấy nút 'Xoá lọc' cạnh các chip đã chọn)."""
        return self._try(self.CLEAR_FILTER, timeout=timeout) is not None

    def clear_filters(self):
        btn = self._try(self.CLEAR_FILTER, timeout=3)
        if btn is None:
            raise UiNotFound("Không thấy nút 'Xoá lọc' (chưa có bộ lọc nào được chọn?)")
        before_u = self.driver.current_url
        self._native_click(btn)
        self._wait_url_change(before_u, 6)
        self._wait_stable()
        self.snapshot("Đã bấm 'Xoá lọc'")
        return self

    def _sort_via_ui(self, label, before_url):
        """Thao tác ô 'Sắp xếp theo' (Radix Select: phải bấm thật để mở, rồi chọn role=option). True nếu URL đã đổi."""
        triggers = self.driver.find_elements(*self.SORT_TRIGGER)
        if not triggers:
            return False
        trigger = next((t for t in triggers if self._shown(t)), triggers[0])
        self._native_click(trigger)
        option = (By.XPATH, self.SORT_OPTION.format(t=label))
        opt = self._try(option, timeout=3)
        if opt is None:                                              # Radix Select cũng mở được bằng bàn phím
            try:
                trigger.send_keys(Keys.ENTER)
            except Exception:
                pass
            opt = self._try(option, timeout=3)
        if opt is None:
            return False
        self._native_click(opt)
        return self._wait_url_change(before_url, 8)

    def sort_by(self, label):
        """Chọn kiểu sắp xếp: thử thao tác ô 'Sắp xếp theo'; nếu không được thì mở thẳng URL có ?sort=...
        (cách chọn ghi trong self.apply_mode và nhật ký chẩn đoán)."""
        before_u = self.driver.current_url
        if self._sort_via_ui(label, before_u) or self._sort_via_ui(label, before_u):
            self.apply_mode = "thao tác ô 'Sắp xếp theo'"
        else:
            param = SORT_PARAMS.get(label)
            if param is None:
                self.snapshot(f"KHONG THAY kieu sap xep '{label}'", shot=True)
                raise UiNotFound(f"Không thao tác được ô sắp xếp và chưa biết tham số URL của '{label}'")
            u = urlparse(before_u)
            query = dict(parse_qsl(u.query))
            query["sort"] = param
            self.driver.get(urlunparse(u._replace(query=urlencode(query))))
            self.apply_mode = f"mở thẳng URL ?sort={param} (không thao tác được ô sắp xếp)"
        self.dismiss_popups()
        self._wait_stable()
        self.snapshot(f"Đã sắp xếp '{label}'")
        return self

    def card_prices(self):
        """Danh sách (giá thấp nhất, giá cao nhất) của từng sản phẩm hiển thị: giá bán và giá gốc nếu có giảm giá."""
        out = []
        for r in self.results():
            p = self.prices_in(r["text"])
            if p:
                out.append((min(p), max(p)))
        return out

    def size_overview(self, timeout=10):
        """{nhãn: 'enabled'|'disabled'} của các nút size CHÍNH trên trang sản phẩm đang mở (chờ trang vẽ xong)."""
        def read(d):
            return [i for i in d.execute_script(JS_PDP_SIZES) if i["shown"]] or False
        try:
            items = WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(read)
        except TimeoutException:
            return {}
        out = {}
        for i in items:
            sold = i["disabled"] or any(t in SOLD_OUT_TOKENS for t in i["cls"].split())
            out.setdefault(i["text"], "disabled" if sold else "enabled")
        return out

    def size_state(self, label, timeout=10):
        """'enabled' = có size và còn hàng, 'disabled' = hết hàng, 'missing' = không có nút size này (ở màu đang mở)."""
        return self.size_overview(timeout).get(label, "missing")

    @staticmethod
    def _fmt_sizes(overview):
        return " ".join(f"{k}:{'còn' if v == 'enabled' else 'hết'}" for k, v in overview.items()) or "(không đọc được nút size)"

    def size_available(self, label):
        """Size còn hàng ở màu đang mở, hoặc ở ít nhất một màu khác của CÙNG sản phẩm (bộ lọc size áp dụng cho sản phẩm).
        Trả về (True/False, ghi chú các màu đã thử)."""
        overview = self.size_overview()
        if overview.get(label) == "enabled":
            return True, ""
        note = f"màu hiện tại: {self._fmt_sizes(overview)}"
        u = urlparse(self.driver.current_url)
        own = dict(parse_qsl(u.query)).get("color")
        for color in [c for c in self.driver.execute_script(JS_PRODUCT_COLORS) if c and c != own][:6]:
            self.driver.get(urlunparse(u._replace(query=urlencode({"color": color}))))
            other = self.size_overview(timeout=8)
            if other.get(label) == "enabled":
                return True, f"còn hàng ở màu '{color}'"
            note += f" | màu '{color}': {self._fmt_sizes(other)}"
        return False, note