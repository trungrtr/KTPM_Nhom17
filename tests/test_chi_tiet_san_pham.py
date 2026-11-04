"""Bảng 4.11 PDP. Run through tools/run_pdp.py to preserve existing reports."""
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait

from pages.product_page import ProductPage
from pages.pdp_support import PDPDataUnavailable
from utils import config  # noqa: F401 - existing .env loading
from utils.test_data import read_csv

pytestmark = [pytest.mark.regression, pytest.mark.pdp]


def required(key):
    value = os.getenv(key, "").strip()
    if not value:
        pytest.skip(f"Thiếu dữ liệu đã xác minh: {key}; xem docs/PDP_MANUAL_TESTS.md")
    return value


def open_page(request, key="PDP_URL_IN_STOCK"):
    url = required(key)  # Resolve prerequisite BEFORE starting a browser.
    driver = request.getfixturevalue("driver")
    request.node.pdp_driver = driver
    try:
        page = ProductPage(driver).open_url(url)
    except PDPDataUnavailable as exc:
        pytest.skip(f"Dữ liệu PDP không phù hợp: {exc}")
    return page


def assert_pdp(page, details_only=False):
    state = page.snapshot(visible_only=True) if details_only else page.snapshot()
    if details_only:
        labels = {"name": "tên SP", "sku": "mã SP hiển thị (không dùng SKU biến thể ẩn)",
                  "price": "giá", "images": "hình ảnh đã tải", "description": "mô tả",
                  "information": "thông tin sản phẩm", "sizes": "size"}
        missing = [f"{key} ({label})" for key, label in labels.items() if not state[key]]
        if not state["in_stock"]:
            missing.append("tình trạng còn hàng (chưa xác minh size đã chọn và nút thêm giỏ khả dụng)")
        assert not missing, (
            "PDP-01 thiếu/chưa đọc được thông tin bắt buộc trên UI: " + "; ".join(missing)
            + ". Kiểm tra DOM/locator và bằng chứng; không suy ra website thiếu chỉ từ locator rỗng."
        )
    for key in ("name", "sku", "price", "images", "description", "information", "sizes"):
        assert state[key], f"PDP thiếu thông tin bắt buộc: {key}"
    assert any(c.isdigit() for c in state["price"]), "Giá không có giá trị số"
    assert all(s["label"] for s in state["sizes"]), "Size không có nhãn"
    assert any(not s["disabled"] for s in state["sizes"]), "Không có size còn hàng"
    if not details_only:
        assert page.elements("add"), "Không có hành động PDP"
    return state


def unchanged_cart_after_reload(page, before):
    # Reload confirms persisted cart state after validation, not a stale badge.
    page.driver.refresh()
    page.dismiss_pdp_overlays()
    page.element("add")
    assert page.cart_count() == before, "Giỏ hàng thay đổi dù thao tác phải bị từ chối"


def test_PDP_01_in_stock_details(request):
    page = open_page(request)
    # Table 4.11: visible details and available sizes; purchase actions belong to PDP-04/05.
    assert_pdp(page, details_only=True)


def test_PDP_02_change_each_color(request):
    path = required("PDP_VARIANT_EXPECTATIONS")
    oracle = json.loads(Path(path).read_text(encoding="utf-8"))
    page = open_page(request)
    page.dismiss_pdp02_popups(initial=True)
    assert urlsplit(oracle["url"]).path == urlsplit(page.driver.current_url).path
    colors = [o["label"] for o in page.options("colors") if not o["disabled"]]
    if len(colors) < 2:
        pytest.skip("Sản phẩm không có ít nhất hai màu còn hàng")
    assert len(colors) == len(set(colors)), "Locator màu không có nhãn duy nhất"
    assert set(colors) == set(oracle["colors"]), "Oracle chưa bao phủ các màu thực tế"
    gallery_failures = []
    sequence = list(colors)
    # A click on an already selected swatch is not a colour transition.
    # Verify the departure with the full oracle before returning to the default.
    if page.selected_labels("colors") == colors[:1]:
        sequence.insert(0, colors[1])
    run_id = time.time_ns()
    for transition_index, color in enumerate(sequence):
        expected = oracle["colors"][color]
        assert expected["price"] and expected["images"] and expected["sizes"], "Oracle không đầy đủ"
        expected_vnd = page.price_vnd(expected["price"])
        last = {}
        previous = None
        stable_since = None
        stable_snapshot = None
        verified_images = None
        target_url = next(e.get_attribute("href") for e in page.elements("colors")
                          if page.label(e) == color)
        target = urlsplit(target_url)
        expected_color_query = parse_qs(target.query).get("color")
        assert expected_color_query, f"Màu {color}: thiếu URL color trên UI"
        checks = {}
        wait_stage = "before_click"

        def condition(actual, wanted):
            return {"status": "PASS" if actual == wanted else "FAIL",
                    "expected": wanted, "actual": actual}

        def image_identity(source):
            # Diagnostic only: strip the known resize option, preserve all other query data.
            parts = urlsplit(source)
            query = parse_qs(parts.query)
            query.pop("aio", None)
            return (parts.scheme, parts.netloc, parts.path,
                    tuple(sorted((k, tuple(v)) for k, v in query.items())))

        def debug(stage):
            evidence = {"stage": stage, "color": color, "url": page.driver.current_url,
                        "expected_raw": expected["price"], "expected_vnd": expected_vnd,
                        "wait_stage": wait_stage, "conditions": checks,
                        "waiting_for": [k for k, v in checks.items() if v["status"] == "FAIL"]}
            print("PDP-02 DEBUG " + json.dumps(evidence, ensure_ascii=False), flush=True)
            # Provenance belongs in the evidence file, never dump HTML into the terminal.
            evidence["observed"] = last
            evidence["native_thumbnail_checks"] = getattr(page, "pdp02_verified_gallery", [])
            try:
                evidence["image_dom"] = page.pdp02_image_debug()
                evidence["gallery_state"] = last["gallery"] if "gallery" in last else page.pdp02_gallery_state()
                image_check = checks.get("images", {})
                extras = set(image_check.get("extra", []))
                print("PDP-02 IMAGES " + json.dumps({
                    "color": color, "selected_color": last.get("selected_colors"),
                    "url": page.driver.current_url, "expected": expected["images"],
                    "actual": last.get("images", []),
                    "missing": image_check.get("missing", []),
                    "extra": sorted(extras),
                    "galleries": [{"index": g["index"], "active_slides": g["activeSlides"],
                        "transform": g["transform"], "scrollLeft": g["scrollLeft"],
                        "running_animations": len(g["animations"]),
                        "displayed_images": [r["currentSrc"] or r["src"] for r in g["images"]
                                             if r["visibleInGallery"]]}
                        for g in evidence["gallery_state"]],
                    "wrong_image_containers": [
                        {"src": row["currentSrc"] or row["src"],
                         "container": row["container"], "ancestors": row["ancestors"]}
                        for row in evidence["image_dom"]
                        if (row["currentSrc"] or row["src"]) in extras
                        or (row["advertising_hint"] and not row["in_gallery"])]
                }, ensure_ascii=False), flush=True)
            except Exception as exc:
                # Diagnostics must not replace the original Timeout with a JS/stale error.
                evidence["image_dom_error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
            folder = Path("results/pdp_evidence")
            folder.mkdir(parents=True, exist_ok=True)
            if stage in ("timeout", "after"):
                try:
                    screenshot = folder / f"pdp02_{run_id}_{transition_index}_{stage}.png"
                    evidence["screenshot"] = str(screenshot)
                    evidence["screenshot_saved"] = page.driver.save_screenshot(str(screenshot))
                    evidence["screenshot_context"] = {
                        "url": page.driver.current_url,
                        "selected_colors": page.selected_labels("colors"),
                        "gallery": page.pdp02_gallery_state()}
                    print(f"PDP-02 SCREENSHOT {screenshot}", flush=True)
                except Exception as exc:
                    evidence["screenshot_error"] = type(exc).__name__
            (folder / f"pdp02_{run_id}_{transition_index}_{stage}.json").write_text(
                json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

        def updated(_):
            nonlocal last, previous, checks, stable_since, stable_snapshot
            # Non-blocking read of the same field as price(); no nested text() wait.
            raw = page.field_text("price")
            try:
                actual_vnd = page.price_vnd(raw)
            except ValueError:
                actual_vnd = None
            gallery = page.pdp02_gallery_state()
            # One browser task supplies image URLs, loading and carousel geometry.
            active_images = [r for g in gallery for r in g["images"] if r["visibleInGallery"]]
            last = {"actual_raw": raw, "actual_vnd": actual_vnd,
                    "delta_vnd": actual_vnd - expected_vnd if actual_vnd is not None else None,
                    "selected_colors": page.selected_labels("colors"),
                    "images": (verified_images if verified_images is not None
                               else page.image_sources(pdp02_gallery=gallery)),
                    "clipped_images": page.image_sources(pdp02_gallery=gallery),
                    "image_scope": "Primary images displayed through native thumbnail clicks",
                    "gallery": gallery,
                    "sizes": {o["label"]: o["disabled"] for o in page.options("sizes")}}
            current = urlsplit(page.driver.current_url)
            checks = {
                "color": condition(last["selected_colors"], [color]),
                "url": condition([current.netloc, current.path, parse_qs(current.query).get("color")],
                                 [target.netloc, target.path, expected_color_query]),
                "price_vnd": condition(actual_vnd, expected_vnd),
                "images": condition(sorted(set(last["images"])), sorted(set(expected["images"]))),
                "sizes_disabled": condition(last["sizes"], expected["sizes"])}
            checks["images"].update(
                missing=sorted(set(expected["images"]) - set(last["images"])),
                extra=sorted(set(last["images"]) - set(expected["images"])),
                same_without_resize=(set(map(image_identity, last["images"])) ==
                                     set(map(image_identity, expected["images"]))))
            checks["sizes_disabled"]["differences"] = {
                s: {"expected": expected["sizes"].get(s), "actual": last["sizes"].get(s)}
                for s in sorted(set(expected["sizes"]) | set(last["sizes"]))
                if s not in expected["sizes"] or s not in last["sizes"]
                or expected["sizes"][s] != last["sizes"][s]}
            checks["gallery_idle"] = condition(
                bool(last["gallery"]) and not any(g["animations"] for g in last["gallery"]), True)
            checks["gallery_loaded"] = condition(
                bool(active_images) and all(r["complete"] and r["naturalWidth"] > 0
                                            for r in active_images), True)
            # Stability is independent of the oracle: stable wrong UI remains FAIL.
            signature = {"images": last["images"], "gallery": gallery}
            now = time.monotonic()
            idle_loaded = all(checks[k]["status"] == "PASS"
                              for k in ("gallery_idle", "gallery_loaded"))
            if not idle_loaded or previous != signature:
                stable_since = now
            stable = idle_loaded and stable_since is not None and now - stable_since >= 1.0
            previous = signature
            checks["stable_two_polls"] = condition(stable, True)
            checks["stable_two_polls"]["reason"] = "Same loaded, idle gallery for at least 1 second"
            last["gallery_stable"] = stable
            if stable:
                stable_snapshot = last
            return last if stable and all(v["status"] == "PASS" for v in checks.values()) else False

        debug("before")
        try:
            wait_stage = "popup_before_click"
            page.dismiss_pdp02_popups()
            wait_stage = "choose_color_selected"
            try:
                page.choose("colors", color)
            except ElementClickInterceptedException:
                # Handle a popup arriving between the preflight and native click.
                page.dismiss_pdp02_popups(initial=True)
                page.choose("colors", color)
            wait_stage = "popup_after_click"
            page.dismiss_pdp02_popups(initial=True)
            wait_stage = "verify_native_gallery_images"
            verified_images = page.pdp02_verify_oracle_images(expected["images"])
            wait_stage = "variant_conditions"
            settled = WebDriverWait(page.driver, float(os.getenv("PDP_TIMEOUT", "30")),
                          poll_frequency=0.5,
                          ignored_exceptions=(StaleElementReferenceException,)).until(
                              updated, message="PDP-02: see per-condition DEBUG; waiting only for failed conditions")
        except TimeoutException as exc:
            # choose()/popup waits can time out before updated() has ever run.
            try:
                updated(None)
            except StaleElementReferenceException:
                pass
            debug("timeout")
            image_check = checks.get("images", {})
            active = [{"slides": g["activeSlides"], "transform": g["transform"],
                       "primary_UI": max(g["images"], key=lambda r: r["clippedArea"])["currentSrc"]
                                     if g["images"] else None,
                       "animations": len(g["animations"]),
                       "images": [{"src": r["currentSrc"] or r["src"],
                                   "clipped_width": max(0, r["clippedRect"]["right"] - r["clippedRect"]["left"]),
                                   "loaded": r["complete"] and r["naturalWidth"] > 0}
                                  for r in g["images"] if r["visibleInGallery"]]}
                      for g in last.get("gallery", [])]
            cause = ("Loaded idle gallery differs from oracle; inspect clipped slide widths and screenshot; "
                     "oracle/scope review required, no website colour defect inferred from filenames"
                     if last.get("gallery_stable") and image_check.get("status") == "FAIL"
                     else f"Conditions did not settle at {wait_stage}")
            failure = (f"PDP-02 FAIL: màu={color!r}; URL={page.driver.current_url}; "
                        f"cause={cause}; expected_images={expected['images']}; "
                        f"actual_images={last.get('images', [])}; "
                        f"missing={image_check.get('missing', [])}; extra={image_check.get('extra', [])}; "
                        f"active_UI/gallery={json.dumps(active, ensure_ascii=False)}; "
                        f"expected={expected['price']!r} ({expected_vnd} VND); "
                        f"actual={last.get('actual_raw')!r} ({last.get('actual_vnd')} VND); "
                        f"chênh lệch={last.get('delta_vnd')} VND; "
                        f"selected={last.get('selected_colors')}; "
                        f"images_match={set(last.get('images', [])) == set(expected['images'])}; "
                        f"sizes_match={last.get('sizes') == expected['sizes']}; "
                        f"stage={wait_stage}; "
                        f"unmet={[k for k, v in checks.items() if v['status'] == 'FAIL']}; {exc.msg}")
            gallery_failures.append(failure)
            continue  # Still inspect Be; retain every failed colour in the final assertion.
        debug("after")
        source = page.variant_price_debug()
        assert any(r["used_by_price"] and r["safe_source"] for r in source["candidates"]), source
        assert page.selected_labels("colors") == [color]
        actual_raw = page.price()
        print(f"PDP-02 DEBUG color={color!r}; page.price()={actual_raw!r}; expected={expected['price']!r}")
        assert page.price_vnd(actual_raw) == expected_vnd, (
            f"{color}: expected={expected['price']!r}, actual={actual_raw!r}; "
            f"delta={page.price_vnd(actual_raw) - expected_vnd} VND")
        assert settled is stable_snapshot
        assert set(settled["images"]) == set(expected["images"]), checks["images"]
        assert {o["label"]: o["disabled"] for o in page.options("sizes")} == expected["sizes"]
    assert not gallery_failures, "\n".join(gallery_failures)


def test_PDP_03_select_each_size(request):
    page = open_page(request)
    colors = [o["label"] for o in page.options("colors") if not o["disabled"]]
    if colors:
        page.choose("colors", colors[0])
    initial = page.size_state()
    sizes = [o["label"] for o in initial["options"] if not o["disabled"]]
    assert len(sizes) == len(set(sizes)), "Size locator returned duplicate labels"
    assert sizes, "Không tìm thấy size khả dụng; kiểm tra locator/dữ liệu"
    if len(sizes) < 2:
        pytest.skip("Cần tối thiểu hai size để kiểm chứng đổi lựa chọn")
    selected = [o["label"] for o in initial["options"] if o["selected"]]
    assert len(selected) <= 1, f"Multiple sizes initially selected: {initial}"
    # Exercise a real change first, then return to the default (including M).
    sequence = [s for s in sizes if s not in selected] + selected
    if not selected:
        sequence += sizes[:1]
    for size in sequence:
        before = page.variant_evidence("sizes")
        previous = None

        def updated(_):
            nonlocal previous
            state = page.size_state()
            rows = state["options"]
            valid = ([r["label"] for r in rows if r["selected"]] == [size]
                     and any(r["label"] == size and not r["disabled"] for r in rows)
                     and state["size_label"] == size)
            # Two consecutive polls reject transient/partially updated renders.
            signature = [(r["label"], r["selected"], r["disabled"]) for r in rows]
            stable = valid and previous == signature
            previous = signature if valid else None
            return state if stable else False

        try:
            page.choose("sizes", size)
            state = page.wait.until(updated, message=f"Size button and UI label updated exclusively: {size}")
            assert [r["label"] for r in state["options"] if r["selected"]] == [size]
            assert page.selected_labels("sizes") == [size], "Size cũ vẫn selected hoặc size mới chưa selected"
        finally:
            page.save_variant_evidence("sizes", size, before)


def test_PDP_04_soldout_variant(request):
    missing_config = [key for key in ("PDP_URL_SOLDOUT", "PDP_SOLDOUT_SIZE", "PDP_SOLDOUT_COLOR")
                      if not os.getenv(key, "").strip()]
    if missing_config:
        pytest.skip("Missing verified sold-out tuple: " + ", ".join(missing_config))
    size = required("PDP_SOLDOUT_SIZE")
    page = open_page(request, "PDP_URL_SOLDOUT")
    color = os.getenv("PDP_SOLDOUT_COLOR", "").strip()
    folder = Path(__file__).resolve().parents[1] / "results" / "pdp_evidence"
    folder.mkdir(parents=True, exist_ok=True)
    stem = folder / f"pdp04_{time.time_ns()}"
    evidence = {"requested_size": size, "requested_color": color,
                "before": None, "after": None, "click": "not attempted"}
    try:
        if color:
            page.choose("colors", color)
        assert page.selected_labels("colors") == [color], "Sold-out color not selected"
        evidence["before"] = page.size_state()
        evidence["selected_before"] = page.selected_labels("sizes")
        assert size not in evidence["selected_before"], "Sold-out size is selected by default"
        # Establish a known available selection, so an unchanged empty/stale
        # selection cannot produce PASS. Never submit this available variant.
        baseline = next((o["label"] for o in page.options("sizes")
                         if o["label"] != size and not o["disabled"]), None)
        assert baseline, "No available baseline size to verify a rejected selection"
        page.choose("sizes", baseline)
        page.dismiss_pdp02_popups(initial=True)
        option = page.option("sizes", size)
        page.scroll_element(option)
        evidence["before"] = page.size_state()
        selected_before = page.selected_labels("sizes")
        evidence["selected_before"] = selected_before
        assert selected_before == [baseline] and size not in selected_before
        assert page.disabled(option), "Biến thể cấu hình không được đánh dấu hết hàng"
        try:
            option.click()  # Ordinary Selenium click; never JS click/attribute mutation.
            evidence["click"] = "native click returned"
        except ElementClickInterceptedException:
            evidence["click"] = "native click intercepted"
            # pointer-events:none hits its own LI. An overlay interception must
            # fail, rather than be mistaken for the site's sold-out protection.
            assert option.value_of_css_property("pointer-events") == "none"
            assert page.driver.execute_script("""
                const e=arguments[0], r=e.getBoundingClientRect();
                const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                return !!hit && e.parentElement.contains(hit);
            """, option), "Click blocked by unrelated overlay; sold-out behavior unverified"
        # Observe across multiple polls; do not accept the first unchanged render.
        deadline = time.monotonic() + 2
        def rejected(_):
            state = page.size_state()
            evidence["after"] = state
            labels = [o["label"] for o in state["options"] if o["selected"]]
            evidence["selected_after"] = labels
            assert size not in labels, "Website selected the sold-out size"
            assert labels == selected_before, "Sold-out click changed selection"
            assert state["size_label"] == baseline, "Purchase UI size differs from baseline"
            assert page.disabled(page.option("sizes", size)), "Sold-out marker disappeared"
            return state if time.monotonic() >= deadline else False
        page.wait.until(rejected)
        # UI purchase eligibility: requested size cannot become the active
        # purchase variant. Add may remain enabled for the available baseline;
        # that is not evidence that the sold-out tuple can be purchased.
        evidence["purchase_ui"] = {
            "active_size": evidence["after"]["size_label"],
            "soldout_size_selected": size in evidence["selected_after"],
            "add": [{"text": e.text, "disabled": page.disabled(e),
                     "html": e.get_attribute("outerHTML")} for e in page.elements("add")],
            "reason": "Sold-out size rejected; purchase UI retains available baseline",
        }
        assert evidence["purchase_ui"]["add"], "Purchase UI unavailable for verification"
        assert not evidence["purchase_ui"]["soldout_size_selected"]
        evidence["outcome"] = "PASS"
    except Exception as exc:
        evidence["outcome"] = "FAIL"
        evidence["reason"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        # Always retain DOM/CSS and before/after selection, including early failures.
        try:
            evidence["after"] = page.size_state()
            evidence["selected_after"] = page.selected_labels("sizes")
            target = page.option("sizes", size)
            stem.with_suffix(".html").write_text(target.get_attribute("outerHTML"), encoding="utf-8")
            page.driver.save_screenshot(str(stem.with_suffix(".png")))
        except Exception as exc:
            evidence["capture_error"] = f"{type(exc).__name__}: {exc}"
        stem.with_suffix(".json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")


def test_PDP_05_add_without_required_variant(request):
    page = open_page(request)
    evidence = {"before": {}, "after": {}, "outcome": "started"}
    folder = Path("results/pdp0205_fix")
    folder.mkdir(parents=True, exist_ok=True)
    stem = folder / f"pdp05_{time.time_ns()}"
    def capture():
        return {"url": page.driver.current_url,
                "selected": {k: page.selected_labels(k) for k in ("sizes", "colors")},
                "options": {k: [{"html": e.get_attribute("outerHTML"),
                                  "displayed": e.is_displayed(), "enabled": e.is_enabled()}
                                 for e in page.raw_elements(k)] for k in ("sizes", "colors", "add")}}
    try:
        page.dismiss_pdp02_popups(initial=True)
        evidence["before"] = capture()
        assert page.options("sizes"), "Chưa xác định được thuộc tính size bắt buộc"
        missing = [key for key in ("colors", "sizes")
                   if page.options(key) and not page.selected_labels(key)]
        if not missing:
            page.try_deselect_variants()
            missing = [key for key in ("colors", "sizes")
                       if page.options(key) and not page.selected_labels(key)]
        if not missing:
            pytest.skip("N/A: native clicks on selected options retain complete color/size; no UI deselection")
        page.dismiss_pdp02_popups()
        before = page.cart_count()
        submitted = page.add_to_cart()
        if submitted:
            page.wait.until(lambda _: page.errors())
            message = page.errors().casefold()
            assert any(word in message for word in ("size", "kích thước", "màu", "color")), message
            assert any(word in message for word in ("chọn", "select", "required")), message
        else:
            assert page.disabled(page.element("add")), "Missing variant must block Add"
        unchanged_cart_after_reload(page, before)
        evidence["outcome"] = "assertions passed"
    except BaseException as exc:
        evidence["outcome"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        try:
            evidence["after"] = capture()
            page.driver.save_screenshot(str(stem) + ".png")
            Path(str(stem) + ".html").write_text(page.driver.page_source, encoding="utf-8")
        except Exception as exc:
            evidence["capture_error"] = str(exc)
        Path(str(stem) + ".json").write_text(
            json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")



QTY_ROWS = read_csv("pdp_qty_valid.csv") + read_csv("pdp_qty_invalid.csv")


@pytest.mark.parametrize("row", QTY_ROWS, ids=[r["quantity"] for r in QTY_ROWS])
def test_PDP_06_quantity(request, row):
    from selenium.common.exceptions import WebDriverException

    value = row["quantity"]
    stage = "open_page"
    try:
        page = open_page(request)
        stage = "locate_controls"
        page.prepare_quantity_controls()

        def actual():
            try:
                return page.quantity_value()
            except (ValueError, TypeError, AssertionError) as exc:
                page.quantity_diagnostics(f"row={value}; cannot read counter: {exc}")
                pytest.fail(f"SELENIUM/UI_MAPPING: Cannot read quantity counter: {exc}")

        def move_to(target):
            nonlocal stage
            current = actual()
            if not 1 <= current <= 10:
                pytest.fail(f"PRECONDITION: Initial quantity={current}; no unbounded clicking")
            for _ in range(abs(target - current)):
                before = actual()
                direction = "plus" if target > before else "minus"
                stage = f"click_{direction}"
                assert page.step_quantity(direction), (
                    f"WEBSITE: {direction} disabled at {before}, target={target}")
                expected = before + (1 if direction == "plus" else -1)
                stage = "observe_after_click"
                try:
                    page.wait.until(lambda _: actual() == expected)
                except TimeoutException:
                    observed = actual()
                    assert observed == expected, (
                        f"WEBSITE: Click {direction}, expected={expected}, actual={observed}")
                assert actual() == expected, f"WEBSITE: Incorrect {direction} step"
                page.quantity_diagnostics(f"after click {direction}; expected={expected}; actual={actual()}")
            assert actual() == target, f"WEBSITE: Expected quantity={target}"

        if value in ("1", "2", "5"):
            # Quantity 1 also requires real native clicks in both directions.
            move_to(1)
            move_to(2)
            move_to(1)
            move_to(int(value))
            assert actual() == int(value), f"WEBSITE: Expected quantity={value}"
            print(f"PDP-06 [{value}] asserted quantity={actual()} via +/-")
            return
        if value == "0":
            move_to(1)
            stage = "click_minus_at_minimum"
            clicked = page.step_quantity("minus")
            stage = "observe_minimum"
            deadline = time.monotonic() + 2

            def remains_one(_):
                observed = actual()
                assert observed == 1, f"WEBSITE: Decrement from 1 must be blocked; actual={observed}"
                return time.monotonic() >= deadline

            page.wait.until(remains_one)
            assert actual() == 1, "WEBSITE: Minimum 1 was not preserved"
            page.quantity_diagnostics(f"after minimum decrement; clicked={clicked}; actual={actual()}")
            print(f"PDP-06 [0] rejected; minus_clicked={clicked}; asserted quantity=1")
            return

        stage = "inspect_ui_reachability"
        counters = page.elements("quantity")
        editable = any(e.tag_name.lower() == "input" and e.is_enabled()
                       and not e.get_attribute("readonly")
                       and e.get_attribute("type") not in ("hidden", "button", "submit")
                       for e in counters)
        if value == "99999":
            if not editable:
                pytest.skip("N/A: 99999 cannot be entered: quantity is not an editable input; "
                            "no mass + clicks performed")
            maximum = [e.get_attribute("max") for e in counters]
            bounded = [int(m) for m in maximum if m and m.isdigit() and 1 <= int(m) < 99999]
            if editable and bounded:
                stage = "native_above_declared_maximum"
                page.set_quantity(value)
                deadline = time.monotonic() + 2
                page.wait.until(lambda _: time.monotonic() >= deadline)
                state = page.quantity_state()
                observed = str(state["value"])
                assert (not state["valid"] or page.errors() or
                        (observed.isdigit() and 1 <= int(observed) <= min(bounded))), (
                    f"WEBSITE: Quantity exceeds declared max={bounded}: {state}")
                print(f"PDP-06 [99999] checked declared max={bounded}: {state}")
                return
            pytest.skip(f"N/A: 99999 maximum not verified; UI max={maximum}, editable={editable}; "
                        "no mass + clicks, no assertion performed")
        if value in ("-1", "abc"):
            if editable:
                move_to(1)
                stage = "native_invalid_input"
                page.set_quantity(value)
                # Blur is sent by set_quantity; allow client validation to settle.
                deadline = time.monotonic() + 2
                page.wait.until(lambda _: time.monotonic() >= deadline)
                field = page.element("quantity")
                observed = field.get_property("value")
                validity = page.quantity_state()
                assert (not validity["valid"] or page.errors() or
                        (str(observed).isdigit() and int(observed) >= 1)), (
                    f"WEBSITE: Invalid quantity {value!r} accepted without validation; "
                    f"observed={observed!r}, state={validity}")
                print(f"PDP-06 [{value}] native input rejected/normalized: {validity}")
                return
            pytest.skip(f"N/A: {value} has no valid +/- UI operation: no editable input; "
                        "buttons change integers only; minimum rejection checked separately in row 0")
        pytest.skip(f"N/A: No verified UI operation/oracle for {value}")
    except AssertionError as exc:
        page.quantity_diagnostics(f"row={value}; stage={stage}; assertion={exc}")
        raise
    except WebDriverException as exc:
        # Preserve Selenium exception and traceback; do not label it a website defect.
        if "page" in locals():
            page.quantity_diagnostics(f"row={value}; stage={stage}; {type(exc).__name__}: {exc.msg}")
        else:
            driver = getattr(request.node, "pdp_driver", None)
            if driver:
                ProductPage(driver).quantity_diagnostics(f"row={value}; stage={stage}; {exc.msg}")
        print(f"PDP-06 SELENIUM_ERROR stage={stage}; {type(exc).__name__}; "
              "website defect not established", flush=True)
        exc.msg = f"PDP-06 SELENIUM_ERROR stage={stage}: {exc.msg}"
        raise


@pytest.mark.manual
@pytest.mark.skip(reason="Manual chưa thực hiện: PDP-07, giá gốc/giảm/%; docs/PDP_MANUAL_TESTS.md")
def test_PDP_07_sale_price_manual():
    """Manual procedure and actual-result form live in docs/PDP_MANUAL_TESTS.md."""


@pytest.mark.manual
@pytest.mark.skip(reason="Manual chưa thực hiện: PDP-08, thumbnail/chuyển ảnh/zoom; docs/PDP_MANUAL_TESTS.md")
def test_PDP_08_gallery_manual():
    """Manual procedure and actual-result form live in docs/PDP_MANUAL_TESTS.md."""


def test_PDP_09_recommended_product(request):
    page = open_page(request)
    try:
        recommendation = page.recommendation()
        href, expected_name = recommendation
        page.follow_recommendation(href)
        assert urlsplit(page.driver.current_url).path.rstrip("/") == urlsplit(href).path.rstrip("/")
        page.wait.until(lambda _: page.text("name").casefold() == expected_name.casefold(),
                        message=f"Recommended PDP name: {expected_name}")
        assert page.text("name").casefold() == expected_name.casefold(), "Tên PDP không khớp sản phẩm gợi ý"
        actual_url, expected_url = urlsplit(page.driver.current_url), urlsplit(href)
        assert actual_url.hostname == expected_url.hostname, "PDP-09 wrong destination host"
        assert actual_url.path.startswith("/product/"), "PDP-09 destination is not a PDP"
        page.recommendation_diagnostics("destination URL and product title verified")
    except Exception as exc:
        page.recommendation_diagnostics(f"PDP-09 failed: {type(exc).__name__}: {exc}")
        raise


@pytest.mark.manual
@pytest.mark.skip(reason="Manual chưa thực hiện: PDP-10, mở/đóng/mở lại bảng size; docs/PDP_MANUAL_TESTS.md")
def test_PDP_10_size_guide_manual():
    """Manual procedure and actual-result form live in docs/PDP_MANUAL_TESTS.md."""
