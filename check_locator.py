"""Kiểm tra locator ứng viên có khớp site thật không (công cụ phụ, không phải test).
Chạy:  python check_locator.py                 -> trang chủ + trang kết quả tìm kiếm "áo thun"
       python check_locator.py "<URL>"         -> quét một trang bất kỳ (ví dụ trang danh mục)
Dòng 'OK' = locator khớp; dòng '--' = chưa khớp (hoặc phần tử chỉ xuất hiện ở trang khác).
"""
import sys

from selenium.webdriver.common.by import By

from pages.home_page import HomePage
from pages.search_page import SearchPage
from utils import driver_factory


def create_driver():
    """Tự tìm hàm tạo driver trong utils/driver_factory.py (tên hàm do TV1 đặt)."""
    for name in ("create_driver", "get_driver", "make_driver", "build_driver", "new_driver"):
        if hasattr(driver_factory, name):
            return getattr(driver_factory, name)()
    funcs = [n for n in dir(driver_factory) if callable(getattr(driver_factory, n)) and not n.startswith("_")]
    raise SystemExit(f"Không đoán được tên hàm tạo driver. Các hàm trong driver_factory.py: {funcs}")


def report(driver, page, label):
    print(f"\n=== {label} ===")
    for name in dir(type(page)):
        val = getattr(type(page), name)
        if (name.isupper() and isinstance(val, tuple) and len(val) == 2
                and all(isinstance(x, str) for x in val) and val[0] in (By.CSS_SELECTOR, By.XPATH)):
            n = len(driver.find_elements(*val))
            print(f"{'OK ' if n else '-- '} {name:20} {n:3}  {val[1][:90]}")


def main():
    driver = create_driver()
    try:
        if len(sys.argv) > 1:
            sp = SearchPage(driver)
            driver.get(sys.argv[1])
            sp.dismiss_popups()
            report(driver, sp, f"Trang chỉ định: {driver.current_url}")
            print("Số sản phẩm gom được:", len(sp.results()))
            print("Giá đọc được (10 đầu):", sp.current_prices()[:10])
            return
        home = HomePage(driver).load()
        report(driver, home, "Trang chủ (HomePage)")
        print("Số link header/footer cùng tên miền:", len(home.internal_links()))
        sp = SearchPage(driver).load()
        report(driver, sp, "Trang chủ (SearchPage)")
        try:
            sp.search("áo thun")
            sp.wait_results()
            print("\nURL kết quả tìm kiếm:", driver.current_url)
            report(driver, sp, "Trang kết quả tìm kiếm")
            print("Số sản phẩm gom được:", len(sp.results()))
        except Exception as e:
            print("\n!! Tìm kiếm lỗi:", type(e).__name__, str(e).splitlines()[0][:150])
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())