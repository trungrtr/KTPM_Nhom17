"""Thành phần dùng chung ở mọi trang (header: tìm kiếm, giỏ hàng, tài khoản)."""
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class Header(BasePage):
    # TODO(TV1/TV3): xác nhận locator trên site thật ở Ngày 2
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[type='search']")
    CART_ICON = (By.CSS_SELECTOR, "a[href*='cart']")

    def search(self, keyword):
        self.type(self.SEARCH_INPUT, keyword)
        self.find(self.SEARCH_INPUT).submit()

    def open_cart(self):
        self.click(self.CART_ICON)
