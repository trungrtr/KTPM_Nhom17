"""Công cụ ĐO (không phải test) cho FLT-04 và FLT-05: với danh sách đã lọc theo size, mở vài sản phẩm đầu và cho biết
  - trang chi tiết có những nút size nào, nút nào trông như 'hết hàng' (disabled, gạch ngang, mờ...) và vì sao,
  - sản phẩm có những màu nào, và size còn/hết có đổi theo màu không.
Chạy:   python inspect_pdp.py        (khoảng 3 đến 5 phút, tự mở và đóng Chrome, không cần bấm gì)
Kết quả in ra màn hình và lưu ở results\\inspect_pdp.txt  ->  gửi file này.
"""
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from pages.search_page import SearchPage
from utils import config, driver_factory

# (đường dẫn danh sách đã lọc, size đã lọc): giống FLT-04 (size S, M) và FLT-05 (màu Đen + giá 200-300k + size L)
SCENARIOS = [
    ("/collection/ao-thun-nam?size=s", "S"),
    ("/collection/ao-thun-nam?size=m", "M"),
    ("/collection/ao-thun-nam-den?price_range=200000-300000&size=l", "L"),
]
PRODUCTS_PER_SCENARIO = 3
OTHER_COLORS_PER_PRODUCT = 2
OUT = Path(__file__).resolve().parent / "results" / "inspect_pdp.txt"

JS_SIZES = r"""
const SIZES = ['XS', 'S', 'M', 'L', 'XL', '2XL', 'XXL', '3XL', '4XL'];
const norm = s => (s || '').replace(/[\u00a0\s]+/g, ' ').trim();
const out = [];
for (const el of document.querySelectorAll('button, a, [role=radio], label')) {
  if (!SIZES.includes(norm(el.textContent))) continue;
  if (el.closest('header,nav,footer')) continue;
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  const reasons = [];
  if (el.disabled) reasons.push('thuộc tính disabled');
  if (el.getAttribute('aria-disabled') === 'true') reasons.push('aria-disabled=true');
  const cm = String(el.className).split(/\s+/).filter(t => ['pointer-events-none', 'cursor-not-allowed', 'line-through'].includes(t));
  if (cm.length) reasons.push('class: ' + cm.join(','));
  if ((cs.textDecorationLine || cs.textDecoration || '').includes('line-through')) reasons.push('chữ gạch ngang');
  if (parseFloat(cs.opacity) < 1) reasons.push('opacity ' + cs.opacity);
  out.push({text: norm(el.textContent), tag: el.tagName.toLowerCase(), reasons: reasons,
            displayed: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none',
            selected: ['aria-pressed', 'aria-checked'].some(a => el.getAttribute(a) === 'true') ||
                      ['on', 'checked', 'active'].includes(el.getAttribute('data-state')),
            cls: String(el.className).slice(0, 90), html: el.outerHTML.replace(/\s+/g, ' ').slice(0, 200)});
}
return out;
"""

JS_COLORS = r"""
const colors = new Set();
document.querySelectorAll('a[href*="color="]').forEach(a => {
  try { const u = new URL(a.href); if (u.pathname === location.pathname) colors.add(u.searchParams.get('color')); } catch (e) {}
});
return [...colors];
"""


def emit(text=""):
    print(text)
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(text + "\n")


def create_driver():
    for name in ("create_driver", "get_driver", "make_driver", "build_driver", "new_driver"):
        if hasattr(driver_factory, name):
            return getattr(driver_factory, name)()
    raise SystemExit("Không tìm thấy hàm tạo driver trong utils/driver_factory.py")


def fresh_listing(d, path):
    d.get(config.BASE_URL.rstrip("/") + "/robots.txt")
    d.execute_script("try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}")
    d.delete_all_cookies()
    page = SearchPage(d).open_collection(path)
    return page.hrefs()


def read_sizes(d):
    for _ in range(20):                                   # chờ trang sản phẩm vẽ xong nút size (tối đa ~10 giây)
        sizes = [s for s in d.execute_script(JS_SIZES) if s["displayed"]]
        if sizes:
            return sizes
        time.sleep(0.5)
    return []


def describe(d, label, wanted):
    sizes = read_sizes(d)
    if not sizes:
        emit(f"   {label}: KHÔNG thấy nút size nào đang hiển thị")
        return
    line = " ".join(f"{s['text']}:{'HẾT?' if s['reasons'] else 'còn'}{'*' if s['selected'] else ''}" for s in sizes)
    emit(f"   {label}: {line}   (dấu * = đang được chọn sẵn)")
    mine = [s for s in sizes if s["text"] == wanted]
    emit(f"      size đã lọc '{wanted}': " + (("trông như HẾT HÀNG vì " + "; ".join(mine[0]["reasons"])) if mine and mine[0]["reasons"]
                                             else ("còn hàng" if mine else "KHÔNG có nút này")))
    shown = {"hết": [s for s in sizes if s["reasons"]][:2], "còn": [s for s in sizes if not s["reasons"]][:1]}
    for kind, items in shown.items():
        for s in items:
            emit(f"      mẫu nút '{kind}': <{s['tag']}> class='{s['cls']}'")
            emit(f"         html: {s['html']}")


def main():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("", encoding="utf-8")
    d = create_driver()
    try:
        for path, size in SCENARIOS:
            emit(f"\n##### Danh sách đã lọc: {path}  (size lọc = {size}) #####")
            try:
                hrefs = fresh_listing(d, path)
            except Exception as e:
                emit(f"  LỖI khi mở danh sách: {type(e).__name__}")
                continue
            emit(f"  số sản phẩm trong khung chính: {len(hrefs)}; mở {min(PRODUCTS_PER_SCENARIO, len(hrefs))} sản phẩm đầu")
            for href in hrefs[:PRODUCTS_PER_SCENARIO]:
                emit(f"\n  --- Sản phẩm: {href}")
                try:
                    d.get(href)
                    SearchPage(d).dismiss_popups()
                    own_color = (parse_qs(urlparse(href).query).get("color") or ["(không có)"])[0]
                    describe(d, f"màu '{own_color}' (đúng liên kết từ danh sách)", size)
                    colors = [c for c in d.execute_script(JS_COLORS) if c and c != own_color]
                    emit(f"   các màu khác của sản phẩm: {colors if colors else '(không tìm thấy liên kết màu)'}")
                    for c in colors[:OTHER_COLORS_PER_PRODUCT]:
                        d.get(f"{config.BASE_URL.rstrip('/')}{urlparse(href).path}?color={c}")
                        describe(d, f"màu '{c}'", size)
                except Exception as e:
                    emit(f"   LỖI: {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        emit("\nXONG. Hãy gửi file results\\inspect_pdp.txt.")
    finally:
        d.quit()


if __name__ == "__main__":
    sys.exit(main())