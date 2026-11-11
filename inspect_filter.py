"""Công cụ ĐO (không phải test): mở trang danh mục thật, với từng nhãn bộ lọc cho biết
  - trang có bao nhiêu phần tử mang chữ đó, loại phần tử nào, nằm ở đâu, có hiển thị không,
  - bấm vào có làm URL đổi không (bấm thật bằng Selenium, rồi bấm bằng JavaScript nếu chưa được),
  - các sản phẩm giá 200.000đ nằm ở đâu trên trang (đã gây lỗi lọc giá), và khung chứa danh sách sản phẩm chính.
Chạy:   python inspect_filter.py        (khoảng 2 đến 4 phút, tự mở và đóng Chrome, không cần bấm gì)
Kết quả in ra màn hình và lưu ở results\\inspect_filter.txt  ->  gửi file này cho người hỗ trợ.
"""
import re
import sys
import time
from pathlib import Path

from selenium.webdriver.common.by import By

from pages.search_page import SearchPage
from utils import config, driver_factory

PATH = "/collection/ao-thun-nam"
LABELS = ["S", "M", "Đen", "Trắng", "Xanh lá", "0 - 200.000đ", "200.000đ - 300.000đ", "300.000đ - 500.000đ", ">500.000đ"]
HEADERS = ["Kích thước", "Màu sắc", "Giá"]
OUT = Path(__file__).resolve().parent / "results" / "inspect_filter.txt"
SHOTS = Path(__file__).resolve().parent / "evidence" / "auto"

# Chuẩn hóa chữ: NFC, gộp mọi loại khoảng trắng (kể cả NBSP), gạch dài -> gạch ngắn, chữ thường
JS_NORM = r"""
const norm = s => (s || '').normalize('NFC').replace(/[\u00a0\u2007\u202f\u200b\s]+/g, ' ')
                           .replace(/[\u2013\u2014\u2212]/g, '-').trim().toLowerCase();
"""

JS_PROBE = JS_NORM + r"""
const label = arguments[0];
const want = norm(label);
const els = [], info = [];
for (const el of document.querySelectorAll('body *')) {
  const tag = el.tagName.toUpperCase();
  if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') continue;
  if (norm(el.textContent) !== want) continue;
  let childMatch = false;
  for (const c of el.children) { if (norm(c.textContent) === want) { childMatch = true; break; } }
  const r = el.getBoundingClientRect();
  const parents = [];
  let p = el.parentElement;
  for (let i = 0; i < 3 && p; i++, p = p.parentElement) parents.push(p.tagName.toLowerCase() + '.' + String(p.className).slice(0, 40));
  els.push(el);
  info.push({tag: tag.toLowerCase(), cls: String(el.className).slice(0, 70), childMatch: childMatch,
             raw: (el.textContent || '').trim() === label,
             x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height),
             parents: parents.join(' < '), html: el.outerHTML.replace(/\s+/g, ' ').slice(0, 220)});
  if (els.length >= 8) break;
}
return {els: els, info: info};
"""

JS_HAS_CLEAR = JS_NORM + r"""
return [...document.querySelectorAll('button,a,span,div')].some(
  e => e.children.length < 3 && /^(xoá|xóa) (bộ )?lọc$/.test(norm(e.textContent)));
"""

JS_GRID = r"""
const sel = "a[href*='/product/']";
const all = document.querySelectorAll(sel);
// bỏ qua liên kết sản phẩm nằm trong menu/chân trang: lấy sản phẩm đầu tiên của danh sách chính
const a = [...all].find(x => !x.closest('header,nav,footer')) || all[0];
const chain = [];
let n = a;
for (let i = 0; i < 8 && n; i++, n = n.parentElement)
  chain.push(i + ' <' + n.tagName.toLowerCase() + ' class="' + String(n.className).slice(0, 70) + '"> số sản phẩm bên trong=' + n.querySelectorAll(sel).length);
const priceRe = /\d{1,3}(\.\d{3})+\s*đ/;
const odd = [];
all.forEach(x => {
  let c = x;
  for (let i = 0; i < 6 && c.parentElement && !priceRe.test(c.innerText || ''); i++) c = c.parentElement;
  if (/200\.000\s*đ/.test(c.innerText || '')) {
    const r = c.getBoundingClientRect();
    odd.push((x.getAttribute('href') || '').slice(0, 55) + ' | x=' + Math.round(r.left) + ' y=' + Math.round(r.top) +
             ' | trong header/menu: ' + !!x.closest('header,nav') + ' | trong footer: ' + !!x.closest('footer') +
             ' | cha: ' + x.parentElement.tagName.toLowerCase() + '.' + String(x.parentElement.className).slice(0, 30));
  }
});
return {total: all.length, chain: chain, odd: odd.slice(0, 10)};
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


def safe_displayed(el):
    try:
        return el.is_displayed()
    except Exception:
        return False


def fresh(d):
    """Mở lại trang danh mục sạch (xóa bộ nhớ trình duyệt để trạng thái bộ lọc cũ không ảnh hưởng)."""
    d.get(config.BASE_URL.rstrip("/") + "/robots.txt")
    d.execute_script("try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}")
    d.delete_all_cookies()
    d.get(config.BASE_URL.rstrip("/") + PATH)
    SearchPage(d).dismiss_popups()
    time.sleep(4)


def grid_report(d, title):
    emit(f"--- {title} ---")
    g = d.execute_script(JS_GRID)
    emit(f"URL: {d.current_url}")
    emit(f"Tổng số liên kết sản phẩm trên trang: {g['total']}")
    emit("Chuỗi cha của sản phẩm đầu tiên (tìm khung chứa danh sách chính = dòng có số sản phẩm gần bằng tổng):")
    for line in g["chain"]:
        emit("   " + line)
    emit(f"Sản phẩm giá 200.000đ ({len(g['odd'])} mục đầu):")
    for line in g["odd"]:
        emit("   " + line)


def probe(d, label):
    r = d.execute_script(JS_PROBE, label)
    return r["els"], r["info"]


def candidates(els, info):
    shown = [e for e, i in zip(els, info) if not i["childMatch"] and safe_displayed(e)]
    return shown or [e for e in els if safe_displayed(e)]


def native_click(d, el):
    d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.6)
    el.click()


def try_click(d, el, label):
    before = d.current_url
    try:
        native_click(d, el)
        how = "bấm thật (Selenium)"
    except Exception as e:
        how = f"bấm thật LỖI {type(e).__name__}"
    time.sleep(3)
    after = d.current_url
    emit(f"  {how}: URL {'ĐỔI' if after != before else 'KHÔNG đổi'} -> {after}")
    if after == before:
        try:
            d.execute_script("arguments[0].click();", el)
            time.sleep(3)
            emit(f"  bấm bằng JavaScript: URL {'ĐỔI' if d.current_url != before else 'KHÔNG đổi'} -> {d.current_url}")
        except Exception as e:
            emit(f"  bấm bằng JavaScript LỖI {type(e).__name__}")
    emit(f"  thấy chip/nút 'Xoá lọc': {d.execute_script(JS_HAS_CLEAR)}")
    try:
        SHOTS.mkdir(parents=True, exist_ok=True)
        d.save_screenshot(str(SHOTS / ("INSPECT_" + re.sub(r"\W+", "_", label)[:30] + ".png")))
    except Exception:
        pass


def inspect_label(d, label):
    emit(f"\n=== Nhãn '{label}' ===")
    fresh(d)
    els, info = probe(d, label)
    xp = len(d.find_elements(By.XPATH, SearchPage.FILTER_OPTION.format(t=label)))
    emit(f"  phần tử mang chữ này (đã chuẩn hóa khoảng trắng/dấu): {len(els)} | XPath chữ-khớp-hoàn-toàn mà test đang dùng khớp: {xp}")
    for i, (e, inf) in enumerate(zip(els, info)):
        emit(f"   [{i}] <{inf['tag']}> class='{inf['cls']}' x={inf['x']} y={inf['y']} {inf['w']}x{inf['h']} "
             f"hiển thị={safe_displayed(e)} chữ-gốc-giống-hệt={inf['raw']} có-con-cũng-khớp={inf['childMatch']}")
        emit(f"       cha: {inf['parents']}")
        emit(f"       html: {inf['html']}")
    cands = candidates(els, info)
    if not cands:
        emit("  KHÔNG có phần tử nào đang hiển thị -> thử mở lần lượt các nhóm bộ lọc")
        for h in HEADERS:
            h_els, h_info = probe(d, h)
            h_c = candidates(h_els, h_info)
            if not h_c:
                emit(f"   nhóm '{h}': không thấy tiêu đề")
                continue
            try:
                native_click(d, h_c[0])
                time.sleep(1.5)
            except Exception as e:
                emit(f"   nhóm '{h}': bấm lỗi {type(e).__name__}")
                continue
            els, info = probe(d, label)
            cands = candidates(els, info)
            emit(f"   sau khi bấm tiêu đề '{h}': phần tử '{label}' hiển thị = {len(cands)}")
            if cands:
                break
    if cands:
        try_click(d, cands[0], label)
    else:
        emit("  Không bấm được vì không có phần tử hiển thị.")


def main():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("", encoding="utf-8")
    d = create_driver()
    try:
        emit(f"Trang kiểm tra: {config.BASE_URL.rstrip('/')}{PATH}")
        fresh(d)
        grid_report(d, "A. Trang danh mục khi CHƯA lọc")
        emit("\n--- B. Tiêu đề các nhóm bộ lọc ---")
        for h in HEADERS:
            els, info = probe(d, h)
            emit(f"  '{h}': {len(els)} phần tử, hiển thị {sum(1 for e in els if safe_displayed(e))}")
        for label in LABELS:
            try:
                inspect_label(d, label)
            except Exception as e:
                emit(f"  LỖI khi đo '{label}': {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        emit("\n=== C. Sau khi chọn khoảng giá '300.000đ - 500.000đ' ===")
        try:
            fresh(d)
            els, info = probe(d, "300.000đ - 500.000đ")
            c = candidates(els, info)
            if not c:
                for h in HEADERS:
                    h_els, h_info = probe(d, h)
                    h_c = candidates(h_els, h_info)
                    if h_c:
                        native_click(d, h_c[0]); time.sleep(1.5)
                        els, info = probe(d, "300.000đ - 500.000đ"); c = candidates(els, info)
                        if c:
                            break
            if c:
                try:
                    native_click(d, c[0])
                except Exception:
                    d.execute_script("arguments[0].click();", c[0])
                time.sleep(5)
                grid_report(d, "Trang sau khi chọn khoảng giá")
            else:
                emit("  không chọn được khoảng giá nên bỏ qua phần này")
        except Exception as e:
            emit(f"  LỖI: {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        emit("\n=== D. Ô sắp xếp ===")
        try:
            fresh(d)
            els, info = probe(d, "Mặc định")
            emit(f"  phần tử 'Mặc định': {len(els)}")
            for i, (e, inf) in enumerate(zip(els, info)):
                emit(f"   [{i}] <{inf['tag']}> class='{inf['cls']}' x={inf['x']} y={inf['y']} hiển thị={safe_displayed(e)}")
                emit(f"       html: {inf['html']}")
            c = candidates(els, info)
            if c:
                native_click(d, c[0]); time.sleep(1.5)
                els2, info2 = probe(d, "Giá thấp đến cao")
                emit(f"  sau khi bấm: phần tử 'Giá thấp đến cao' = {len(els2)}, hiển thị = {sum(1 for e in els2 if safe_displayed(e))}")
                for i, (e, inf) in enumerate(zip(els2, info2)):
                    emit(f"   [{i}] <{inf['tag']}> class='{inf['cls']}' hiển thị={safe_displayed(e)} html: {inf['html']}")
                c2 = candidates(els2, info2)
                if c2:
                    try_click(d, c2[0], "sap xep tang")
        except Exception as e:
            emit(f"  LỖI: {type(e).__name__}: {str(e).splitlines()[0][:150]}")
        emit("\nXONG. Hãy gửi file results\\inspect_filter.txt (và ảnh evidence\\auto\\INSPECT_*.png nếu có).")
    finally:
        d.quit()


if __name__ == "__main__":
    sys.exit(main())