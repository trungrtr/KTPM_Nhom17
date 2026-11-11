"""Dùng chung MỘT trình duyệt cho cả lượt chạy các file test của TV3 (thay vì mở Chrome mới ở mỗi test, mất ~55 giây/lần).
Chỉ test_search, test_filter, test_ui import fixture này nên test của người khác không bị ảnh hưởng.
Muốn quay lại cách cũ (mỗi test một Chrome): xóa hai dòng `from tests import browser_session` và `driver = ...` trong file test.
"""
import pytest

from utils import driver_factory

_STATE = {"driver": None, "registered": False}


def _make_driver():
    """Tạo driver bằng đúng hàm trong utils/driver_factory.py của nhóm (tên hàm do TV1 đặt)."""
    for name in ("create_driver", "get_driver", "make_driver", "build_driver", "new_driver"):
        if hasattr(driver_factory, name):
            return getattr(driver_factory, name)()
    funcs = [n for n in dir(driver_factory) if callable(getattr(driver_factory, n)) and not n.startswith("_")]
    raise RuntimeError(f"Không đoán được tên hàm tạo driver. Các hàm trong driver_factory.py: {funcs}")


def _alive(d):
    try:
        d.title
        return True
    except Exception:
        return False


def _quit_shared():
    d, _STATE["driver"] = _STATE["driver"], None
    if d is not None:
        try:
            d.quit()
        except Exception:
            pass


@pytest.fixture
def driver(request):
    d = _STATE["driver"]
    if d is not None and not _alive(d):               # Chrome cũ đã chết -> tạo lại
        d = None
    if d is None:
        d = _make_driver()
        _STATE["driver"] = d
        if not _STATE["registered"]:                  # đóng Chrome một lần khi kết thúc cả lượt chạy
            request.config.add_cleanup(_quit_shared)
            _STATE["registered"] = True
    yield d
    try:                                              # dọn trạng thái giữa các test (site có thể nhớ bộ lọc đã chọn)
        d.execute_script("try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}")
    except Exception:
        pass
    try:
        d.delete_all_cookies()
        d.get("about:blank")
    except Exception:
        pass                                                                                                            