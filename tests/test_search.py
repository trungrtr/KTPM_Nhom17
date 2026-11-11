"""Test module Tìm kiếm (SRC) - phụ trách: TV3 (Lâm).
SRC-13 (autocomplete) là loại M - chạy tay, không có script.
Tên hàm bắt buộc dạng test_SRC_xx_... để conftest.py lấy đúng TC ID.
"""
import csv
import os
import statistics
import unicodedata
from pathlib import Path

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from pages.search_page import SearchPage
from utils import config
from utils.test_data import read_csv

ROOT = Path(__file__).resolve().parent.parent

# ---- Dữ liệu kiểm thử (Data-driven) đọc từ thư mục data/
OTHER_KEYWORDS = read_csv("src_other_keywords.csv")
SPECIAL_CHARS = read_csv("src_special_chars.csv")
MULTIWORD = read_csv("src_multiword.csv")

from tests import browser_session

driver = browser_session.driver      # dùng chung một Chrome cho cả file (nhanh hơn)

smoke = pytest.mark.smoke
regression = pytest.mark.regression
high = pytest.mark.high
medium = pytest.mark.medium


@pytest.fixture
def sp(driver):
    return SearchPage(driver).load()


def search_and_wait(sp, keyword, timeout=10):
    sp.search(keyword)
    sp.wait_results(timeout)
    return sp


def norm(text):
    """Chữ thường, bỏ dấu tiếng Việt: 'Áo Thun' -> 'ao thun'."""
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def relevance(results, keyword):
    """Tỉ lệ thẻ sản phẩm chứa ĐỦ MỌI từ của từ khóa (không phân biệt dấu).
    Phải đủ mọi từ: chỉ cần một từ thì danh sách gợi ý (áo khoác, áo polo...) cũng bị tính là liên quan với 'áo thun'."""
    tokens = [norm(t) for t in keyword.split() if t]
    if not results or not tokens:
        return 0.0
    hit = sum(1 for r in results if all(t in norm(r["text"]) for t in tokens))
    return hit / len(results)


def search_relevant(page, keyword, patience=25):
    """Tìm kiếm rồi chờ (tối đa `patience` giây) cho tới khi kết quả liên quan từ khóa.
    Trang tìm kiếm hiện danh sách gợi ý trước, kết quả thật tới sau nên không được dừng quá sớm.
    Trả về tỉ lệ liên quan cuối cùng."""
    page.search(keyword)
    page.wait_results()
    try:
        WebDriverWait(page.driver, patience, poll_frequency=1).until(
            lambda d: relevance(page.results(), keyword) >= 0.5)
    except TimeoutException:
        pass
    return relevance(page.results(), keyword)


# ---------------------------------------------------------------- SRC-01
@smoke
@high
def test_SRC_01_search_by_keyword(sp):
    rel = search_relevant(sp, "áo thun")
    assert sp.results(), "Không có sản phẩm nào cho từ khóa 'áo thun'"
    assert rel >= 0.5, f"Chỉ {rel:.0%} sản phẩm chứa đủ các từ 'áo thun' (cần ít nhất 50%)"


# ---------------------------------------------------------------- SRC-02
@regression
@high
@pytest.mark.parametrize("row", OTHER_KEYWORDS, ids=[r["tc_id"] for r in OTHER_KEYWORDS])
def test_SRC_02_search_other_keywords(sp, row):
    keyword = row["keyword"]
    rel = search_relevant(sp, keyword)
    assert sp.results(), f"Không có kết quả cho '{keyword}'"
    assert rel >= 0.5, f"Chỉ {rel:.0%} sản phẩm chứa đủ các từ '{keyword}' (cần ít nhất 50%)"


# ---------------------------------------------------------------- SRC-03
@regression
@medium
def test_SRC_03_accent_insensitive(driver):
    page_a = SearchPage(driver).load()
    rel_a = search_relevant(page_a, "áo thun")
    a = page_a.product_slugs()
    page_b = SearchPage(driver).load()
    rel_b = search_relevant(page_b, "ao thun")
    b = page_b.product_slugs()
    assert a and b, "Một trong hai cách gõ không có kết quả"
    assert rel_a >= 0.5, f"'áo thun' chỉ có {rel_a:.0%} kết quả liên quan"
    assert rel_b >= 0.5, f"'ao thun' (không dấu) chỉ có {rel_b:.0%} kết quả liên quan"
    union = set(a) | set(b)
    overlap = len(set(a) & set(b)) / len(union)
    assert overlap >= 0.8, f"'áo thun' và 'ao thun' chỉ trùng {overlap:.0%} kết quả"


# ---------------------------------------------------------------- SRC-04
@regression
@medium
def test_SRC_04_case_insensitive(driver):
    sets, rels = [], {}
    for kw in ("ÁO THUN", "áo thun", "Áo Thun"):
        page = SearchPage(driver).load()
        rels[kw] = search_relevant(page, kw)
        sets.append(set(page.product_slugs()))
    assert all(sets), "Có biến thể chữ hoa/thường không ra kết quả"
    low = {k: f"{v:.0%}" for k, v in rels.items() if v < 0.5}
    assert not low, f"Có biến thể trả về sản phẩm KHÔNG liên quan từ khóa (tỉ lệ liên quan): {low}"
    assert sets[0] == sets[1] == sets[2], "Kết quả khác nhau giữa chữ hoa/thường"


# ---------------------------------------------------------------- SRC-05
@smoke
@high
def test_SRC_05_no_result(sp):
    search_and_wait(sp, "asdfghjk")
    assert sp.results() == [], "Từ khóa vô nghĩa vẫn trả về sản phẩm"
    assert sp.has_no_result_message(), "Không hiển thị thông báo 'không tìm thấy'"


# ---------------------------------------------------------------- SRC-06 / 07
@regression
@medium
def test_SRC_06_empty_keyword(sp):
    search_and_wait(sp, "", timeout=3)
    assert sp.page_is_healthy(), "Trang lỗi khi tìm kiếm rỗng"
    assert config.BASE_URL.split("//")[-1].split("/")[0] in sp.driver.current_url


@regression
@medium
def test_SRC_07_whitespace_keyword(sp):
    search_and_wait(sp, "     ", timeout=3)
    assert sp.page_is_healthy(), "Trang lỗi khi tìm kiếm chỉ có khoảng trắng"


# ---------------------------------------------------------------- SRC-08
@regression
@medium
@pytest.mark.parametrize("row", SPECIAL_CHARS, ids=[r["tc_id"] for r in SPECIAL_CHARS])
def test_SRC_08_special_characters(sp, row):
    keyword = row["keyword"]
    search_and_wait(sp, keyword, timeout=5)
    assert sp.page_is_healthy(), f"Trang lỗi với từ khóa đặc biệt {keyword!r}"
    assert sp.results() or sp.has_no_result_message(), "Không có kết quả cũng không có thông báo"


# ---------------------------------------------------------------- SRC-09
@regression
@medium
@pytest.mark.parametrize("row", MULTIWORD, ids=[r["tc_id"] for r in MULTIWORD])
def test_SRC_09_multi_word_keyword(sp, row):
    """Ghi nhận hành vi thực tế: có kết quả hoặc có thông báo rỗng, trang không lỗi."""
    search_and_wait(sp, row["keyword"])
    assert sp.page_is_healthy()
    assert sp.results() or sp.has_no_result_message()


@regression
@medium
def test_SRC_09_search_by_product_code(sp):
    code = os.getenv("SRC_PRODUCT_CODE")
    if not code:
        pytest.skip("Đặt SRC_PRODUCT_CODE trong .env (một mã sản phẩm có thật) để chạy case này")
    search_and_wait(sp, code)
    assert sp.page_is_healthy()
    assert sp.results() or sp.has_no_result_message()


# ---------------------------------------------------------------- SRC-10
@regression
@high
def test_SRC_10_result_card_content(sp):
    search_and_wait(sp, "áo thun")
    cards = sp.results()[:5]
    assert cards, "Không có thẻ sản phẩm để kiểm tra"
    for c in cards:
        assert c["image"], f"Thiếu ảnh: {c['href']}"
        assert c["text"], f"Thiếu tên/nội dung: {c['href']}"
        assert sp.prices_in(c["text"]), f"Thiếu giá hoặc sai định dạng giá: {c['href']}"


# ---------------------------------------------------------------- SRC-11
@regression
@medium
def test_SRC_11_search_response_time(driver):
    keywords = ["áo thun", "quần short", "áo polo", "áo khoác", "tất"]
    rows, times = [], []
    for kw in keywords:
        for run in (1, 2, 3):
            t = SearchPage(driver).timed_search(kw)
            rows.append((kw, run, round(t, 2)))
            times.append(t)
    out = ROOT / "results" / "search_timing.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["keyword", "run", "seconds"])
        w.writerows(rows)
    avg = statistics.mean(times)
    assert avg <= 3.0, f"Thời gian tìm kiếm trung bình {avg:.2f}s > 3s (xem {out.name})"


# ---------------------------------------------------------------- SRC-12
@regression
@medium
def test_SRC_12_long_keyword(sp):
    search_and_wait(sp, "áo thun " * 30, timeout=5)      # 240 ký tự
    assert sp.page_is_healthy(), "Trang lỗi với từ khóa dài"
    assert sp.results() or sp.has_no_result_message()