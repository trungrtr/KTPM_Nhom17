"""Page Object: ProductPage - phụ trách: TV3 - module: PDP.
Quy tắc: locator đặt ở đầu lớp; method là hành động nghiệp vụ; KHÔNG assert trong page.
"""
from selenium.webdriver.common.by import By  # noqa: F401

from pages.base_page import BasePage


class ProductPage(BasePage):
    PATH = ""  # TODO: đường dẫn trang, xác nhận trên site thật

    # TODO: khai báo locator, ví dụ  EMAIL_INPUT = (By.ID, "email")

    def load(self):
        return self.open(self.PATH)
