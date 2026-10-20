from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
 
def test_mo_trang_chu_coolmate():
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://www.coolmate.me/")
        tieu_de = driver.title
        print("Tiêu đề trang:", tieu_de)
        print("Địa chỉ trang:", driver.current_url)
        assert "coolmate" in tieu_de.lower()
        assert "coolmate.me" in driver.current_url
        time.sleep(20) 
    finally:
        driver.quit()
