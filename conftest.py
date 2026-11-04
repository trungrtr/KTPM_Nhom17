"""Fixture dùng chung + hook chụp ảnh khi fail + ghi results/results.csv.

Mỗi lần chạy pytest sẽ tạo CSV mới (không nối thêm vào kết quả cũ).
"""
import csv
from datetime import datetime
from pathlib import Path

import pytest

from utils.driver_factory import create_driver

ROOT = Path(__file__).resolve().parent
RESULTS_CSV = ROOT / "results" / "results.csv"
EVIDENCE_AUTO = ROOT / "evidence" / "auto"


def pytest_sessionstart(session):
    """Xoá CSV cũ khi bắt đầu phiên chạy mới để chỉ lưu kết quả lần chạy mới nhất."""
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if RESULTS_CSV.exists():
        RESULTS_CSV.unlink()


@pytest.fixture
def driver():
    drv = create_driver()
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    drv = item.funcargs.get("driver")
    tc_id = "_".join(item.name.split("_")[1:3])  # test_REG_01_xxx -> REG_01
    if rep.failed and drv:
        EVIDENCE_AUTO.mkdir(parents=True, exist_ok=True)
        drv.save_screenshot(str(EVIDENCE_AUTO / f"{tc_id}_{datetime.now():%Y%m%d_%H%M%S}_FAIL.png"))
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["tc_id", "status", "duration_s", "timestamp", "browser"])
        w.writerow([tc_id.replace("_", "-"), rep.outcome, round(rep.duration, 2),
                    datetime.now().isoformat(timespec="seconds"), "chrome"])
