import time
from selenium import webdriver
 
driver = webdriver.Chrome()
driver.get("https://www.coolmate.me/")
print("Tiêu đề:", driver.title)
time.sleep(3)
driver.quit()
