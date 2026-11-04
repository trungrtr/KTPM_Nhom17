"""Opt-in PDP plugin. Does not load or alter REG/LOG reporting hooks."""
import csv
import os
import html
import importlib.util
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# Reuse the exact existing fixture while keeping its module's hooks unregistered.
spec = importlib.util.spec_from_file_location("_pdp_existing_fixture", ROOT / "conftest.py")
existing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)
driver = existing.driver


def pytest_addoption(parser):
    parser.addoption("--pdp-offline", action="store_true", help="Skip browser execution, explicitly reported")


def pytest_configure(config):
    config.addinivalue_line("markers", "pdp: product detail cases from Bảng 4.11")
    config.addinivalue_line("markers", "manual: pending human execution, never automatic PASS")
    config._pdp_rows = {}
    config._pdp_started = datetime.now().isoformat(timespec="seconds")


@pytest.fixture(autouse=True)
def pdp_execution_mode(request):
    if request.node.get_closest_marker("pdp") and request.config.getoption("--pdp-offline"):
        pytest.skip("Offline: Selenium/Coolmate connectivity unavailable; no UI verification performed")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if not item.get_closest_marker("pdp"):
        return
    parts = item.originalname.split("_")
    case = "-".join(parts[1:3])
    if hasattr(item, "callspec"):
        case += "[" + item.callspec.id + "]"
    state = item.config._pdp_rows.setdefault(item.nodeid, {
        "Test_ID": case, "Status": "PASS", "Duration": 0,
        "Timestamp": datetime.now().isoformat(timespec="seconds"), "Browser": "unavailable",
        "mode": "Manual chưa thực hiện" if item.get_closest_marker("manual") else "Automation",
        "reason": [],
    })
    state["Duration"] += report.duration
    if report.failed:
        state["Status"] = "FAIL"
    elif report.skipped and state["Status"] != "FAIL":
        state["Status"] = "SKIP"
    if report.failed or report.skipped:
        # Only exception type or skip reason; no credentials or stack-local values.
        if report.skipped and isinstance(report.longrepr, tuple):
            state["reason"].append(str(report.longrepr[2]))
        elif call.excinfo:
            state["reason"].append(report.when + ": " + call.excinfo.typename)
    drv = item.funcargs.get("driver") or getattr(item, "pdp_driver", None)
    if drv:
        state["Browser"] = drv.capabilities.get("browserName", "unknown")
    # Screenshots intentionally opt-in: browser popups may expose personal data.
    if report.failed and drv:
        import os
        if os.getenv("PDP_FAILURE_SCREENSHOTS", "false").lower() == "true":
            folder = ROOT / "results" / "pdp_evidence"
            folder.mkdir(parents=True, exist_ok=True)
            destination = folder / (case.replace("[", "_").replace("]", "") + "_" +
                                    datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png")
            try:
                drv.save_screenshot(str(destination))
            except Exception:
                report.sections.append(("PDP evidence", "Screenshot unavailable"))


def pytest_sessionfinish(session, exitstatus):
    if session.config.option.collectonly:
        return
    rows = list(session.config._pdp_rows.values())
    if not rows:
        return
    folder = Path(os.getenv("PDP_REPORT_DIR", str(ROOT / "results")))
    folder.mkdir(parents=True, exist_ok=True)
    fields = ["Test_ID", "Status", "Duration", "Timestamp", "Browser"]
    with (folder / "pdp_test_results.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(dict(row, Duration=round(row["Duration"], 3)) for row in rows)
    columns = fields + ["mode", "reason"]
    body = "".join("<tr>" + "".join("<td>" + html.escape(str(
        round(row[key], 3) if key == "Duration" else "; ".join(row[key]) if key == "reason" else row[key]
    )) + "</td>" for key in columns) + "</tr>" for row in rows)
    content = ("<!doctype html><html lang='vi'><meta charset='utf-8'><title>PDP report</title>"
               "<style>body{font:16px system-ui;margin:2em}table{border-collapse:collapse}"
               "td,th{border:1px solid #bbb;padding:8px;text-align:left}</style>"
               "<h1>PDP — phiên chạy mới nhất</h1><p>Started: " + session.config._pdp_started +
               f"; pytest exit: {exitstatus}</p><p>SKIP không phải PASS. Manual chưa chạy được ghi SKIP.</p>"
               "<table><thead><tr>" + "".join("<th>" + c + "</th>" for c in columns) +
               "</tr></thead><tbody>" + body + "</tbody></table></html>")
    (folder / "pdp_report.html").write_text(content, encoding="utf-8")
