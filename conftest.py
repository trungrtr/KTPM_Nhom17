"""Fixture dùng chung + hook ghi kết quả test case vào results/results.csv.
Theo yêu cầu: không xuất ảnh/screenshot màn hình, ghi rõ log kết quả của test case.
"""
import csv
import logging
from datetime import datetime
from pathlib import Path

import pytest
from utils.driver_factory import create_driver

ROOT = Path(__file__).resolve().parent
RESULTS_CSV = ROOT / "results" / "results.csv"

# Thiết lập logging chuẩn hóa
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("CoolmateTest")


def pytest_sessionstart(session):
    """Khởi tạo session test và tệp lưu trữ kết quả."""
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def driver():
    drv = create_driver()
    yield drv
    try:
        drv.quit()
    except Exception:
        pass


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return

    parts = item.name.split("_")
    if len(parts) >= 3:
        tc_id = f"{parts[1]}-{parts[2]}"
    else:
        tc_id = item.name

    # Ghi log kết quả rõ ràng
    status_label = "PASS" if rep.passed else ("FAIL" if rep.failed else "SKIP")
    logger.info(f">>> TEST CASE {tc_id}: {status_label} (Thời gian thực thi: {round(rep.duration, 2)}s)")

    # Ghi nhận kết quả vào results.csv
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_file = not RESULTS_CSV.exists()
    with open(RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["tc_id", "status", "duration_s", "timestamp", "browser"])
        w.writerow([
            tc_id,
            rep.outcome,
            round(rep.duration, 2),
            datetime.now().isoformat(timespec="seconds"),
            "chrome"
        ])
