"""Conftest riêng cho thư mục tests/ ─ Hook ghi kết quả REG vào CSV.

File CSV đầu ra : results/reg_test_results.csv
Định dạng mỗi dòng: Test_ID,Status,Duration,Timestamp,Browser
Ví dụ            : REG-01,passed,0.08,2026-10-20T22:06:07,chrome

Mỗi lần chạy pytest sẽ tạo CSV mới (không nối thêm vào kết quả cũ).
"""

import csv
from datetime import datetime
from pathlib import Path

# ── Đường dẫn gốc dự án & file CSV ──────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
REG_RESULTS_CSV = ROOT / "results" / "reg_test_results.csv"


def pytest_sessionstart(session):
    """Prepare the existing REG directory without clearing unrelated runs."""
    REG_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(session, config, items):
    """Xoá CSV cũ khi bắt đầu phiên chạy mới để chỉ lưu kết quả lần chạy mới nhất."""
    REG_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if any(item.name.startswith("test_REG_") for item in items) and REG_RESULTS_CSV.exists():
        REG_RESULTS_CSV.unlink()


def pytest_runtest_logreport(report):
    """Tự động ghi / append kết quả mỗi test REG vào file CSV.

    Chỉ xử lý giai đoạn ``call`` (bỏ qua setup / teardown).
    Chỉ ghi các test có prefix ``REG`` trong tên hàm (bỏ qua UI, CART…).
    """
    # 1. Chỉ quan tâm giai đoạn "call" (thực thi hàm test)
    if report.when != "call":
        return

    # 2. Trích tên hàm test, bỏ phần parametrize nếu có
    node_name = report.nodeid.split("::")[-1]
    base_name = node_name.split("[")[0]

    # 3. Tách các phần bằng dấu "_"
    parts = base_name.split("_")
    if len(parts) < 3 or parts[1] != "REG":
        return  # Không phải test REG → bỏ qua

    # 4. Ghép Test_ID: "REG-01"
    tc_id = f"{parts[1]}-{parts[2]}"

    # 5. Tạo thư mục results/ nếu chưa tồn tại
    REG_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)

    # 6. Ghi header khi tạo file mới; append dữ liệu
    new_file = not REG_RESULTS_CSV.exists()
    with open(REG_RESULTS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["Test_ID", "Status", "Duration", "Timestamp", "Browser"])
        writer.writerow([
            tc_id,                                          # REG-01
            report.outcome,                                 # passed | failed | skipped
            round(report.duration, 2),                      # 0.08 | 7.0
            datetime.now().isoformat(timespec="seconds"),   # 2026-10-20T22:06:07
            "chrome",                                       # fix cứng trình duyệt
        ])


# LOG reporting is independent of REG and includes setup skips and teardown errors.
import pytest

LOG_RESULTS_CSV = ROOT / "results" / "log_test_results.csv"
_LOG_REPORTS = {}
_LOG_RUN_ID = None


@pytest.hookimpl(specname="pytest_collection_modifyitems", trylast=True)
def pytest_collection_modifyitems_log(session, config, items):
    global _LOG_RUN_ID
    if not config.option.collectonly and any(item.nodeid.split("::")[0].endswith("test_dang_nhap.py") for item in items):
        _LOG_REPORTS.clear()
        _LOG_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        LOG_RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        if LOG_RESULTS_CSV.exists():
            # Retain previous evidence while the primary CSV describes only this run.
            from shutil import copy2
            archive = LOG_RESULTS_CSV.parent / "log_runs" / _LOG_RUN_ID
            archive.mkdir(parents=True, exist_ok=True)
            copy2(LOG_RESULTS_CSV, archive / "previous_log_test_results.csv")
        with LOG_RESULTS_CSV.open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow(["Test_ID", "Status", "Duration", "Timestamp", "Browser",
                                        "Node_ID", "Run_ID", "Phases"])


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not item.nodeid.split("::")[0].endswith("test_dang_nhap.py"):
        return
    drv = (getattr(item, "log_driver", None) or item.funcargs.get("driver")
           or item.funcargs.get("login_driver"))
    if report.failed and drv:
        # LOG-only evidence: never serialize cookies, page source or input values.
        import json
        import os
        from urllib.parse import urlsplit
        from pages.login_page import LoginPage
        try:
            page = LoginPage(drv)
            url = urlsplit(drv.current_url)
            evidence = {
                "url": url.scheme + "://" + url.netloc + url.path,
                "phase": report.when,
                "exception": type(call.excinfo.value).__name__ if call.excinfo else None,
                "errors": page.errors((page.IDENTITY_INPUT, page.PASSWORD_INPUT)),
                "challenge": page.challenge(),
                "authenticated_controls": page.authenticated(),
                "inputs": drv.execute_script(
                    "return Array.from(document.querySelectorAll('input')).map(e=>"
                    "({tag:e.tagName,type:e.type,name:e.name,required:e.required,"
                    "disabled:e.disabled,invalid:!e.validity.valid}));"),
            }
            payload = json.dumps(evidence, ensure_ascii=False, indent=2)
            for key, value in os.environ.items():
                if value and any(word in key for word in ("PASSWORD", "EMAIL", "PHONE", "TOKEN", "SECRET")):
                    payload = payload.replace(value, "[REDACTED]")
            destination = ROOT / "results" / "log_runs" / (_LOG_RUN_ID or "unassigned") / (
                item.name + "_" + report.when + "_diagnostic.json")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(payload, encoding="utf-8")
        except Exception:
            # Evidence failure must not replace the original test outcome.
            report.sections.append(("LOG diagnostics", "Browser evidence unavailable"))
    browser = getattr(item, "log_browser", None) or (
        drv.capabilities.get("browserName", "unknown") if drv else "unavailable")
    phases = _LOG_REPORTS.setdefault(item.nodeid, [])
    phases.append((report.outcome, report.duration, browser))
    if report.when == "teardown":
        status = "failed" if any(r[0] == "failed" for r in phases) else (
            "skipped" if any(r[0] == "skipped" for r in phases) else "passed")
        manual_skip = item.get_closest_marker("skip")
        if (item.name in ("test_LOG_12_logout_and_back", "test_LOG_14_forgot_password")
                and manual_skip is not None
                and manual_skip.kwargs.get("reason") == "Manual Testing"
                and any(r[0] == "skipped" for r in phases)):
            status = "manual"  # Pending human execution; never an automatic verdict.
        browsers = [r[2] for r in phases if r[2] != "unavailable"]
        with LOG_RESULTS_CSV.open("a", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow([
                "-".join(item.name.split("_")[1:3]), status,
                round(sum(r[1] for r in phases), 3),
                datetime.now().isoformat(timespec="seconds"), browsers[-1] if browsers else "unavailable",
                item.nodeid, _LOG_RUN_ID, ";".join(r[0] for r in phases),
            ])
        _LOG_REPORTS.pop(item.nodeid, None)
