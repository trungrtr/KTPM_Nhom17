import pytest

from pages.home_page import HomePage


@pytest.mark.smoke
@pytest.mark.high
def test_UI_01_open_home_page(driver):
    """UI-01: Truy cập trang chủ trên Chrome (TC01)."""
    home = HomePage(driver).load()
    assert "coolmate" in home.title().lower()
