from pages.base_page import BasePage


class HomePage(BasePage):
    PATH = "/"

    def load(self):
        return self.open(self.PATH)

    def title(self):
        return self.driver.title
