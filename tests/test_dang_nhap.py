"""Bang 4.8: 14 LOG cases. See docs/LOG_TESTS.md for prerequisites.

Credentials are loaded by utils.config from .env. No CAPTCHA bypass.
"""
import os
import uuid

import pytest
from requests.exceptions import RequestException
from selenium.common.exceptions import WebDriverException

from pages.login_page import LoginPage
from utils import config  # noqa: F401 - loads .env before required()

pytestmark = pytest.mark.regression


def required(key):
    value = os.getenv(key, "")
    if not value:
        pytest.skip(f"Missing .env prerequisite: {key}")
    return value


def credentials():
    return required("TEST_EMAIL"), required("TEST_PASSWORD")


def wrong_password(password):
    # Keep length/character classes so client length limits do not mask rejection.
    first = password[0]
    choices = "0123456789" if first.isdigit() else (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if first.isupper() else (
            "abcdefghijklmnopqrstuvwxyz" if first.isalpha() else "!@#$%&*"))
    replacement = next(c for c in choices if c != first)
    return replacement + password[1:]


@pytest.fixture
def login_driver(request):
    # Reuse the existing driver fixture; infrastructure failures remain errors.
    try:
        drv = request.getfixturevalue("driver")
    except (WebDriverException, RequestException, OSError) as exc:
        raise RuntimeError(f"Selenium infrastructure unavailable: {type(exc).__name__}") from exc
    request.node.log_driver = drv
    request.node.log_browser = drv.capabilities.get("browserName", "unknown")
    try:
        yield drv
    finally:
        page = getattr(request.node, "log_page", None)
        if page is not None:
            try:
                save_log01_evidence(page, request.node.name)
            except OSError as exc:
                request.node.add_report_section("teardown", "LOG evidence", type(exc).__name__)



def page_of(request):
    page = LoginPage(request.getfixturevalue("login_driver"))
    if request.node.name.startswith('test_LOG_08_email_format_and_spaces[') or request.node.name in (
            'test_LOG_08_email_format_and_spaces', 'test_LOG_09_case_sensitivity',
            'test_LOG_09_password_case_sensitivity',
            'test_LOG_11_password_visibility', 'test_LOG_12_logout_and_back',
            'test_LOG_14_forgot_password'):
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By
        page.failed_log_debug = True
        page.wait = WebDriverWait(page.driver, config.DEFAULT_TIMEOUT,
                                 ignored_exceptions=(StaleElementReferenceException,))
        # name=address is recorded in the failed recovery DOM, not inferred.
        if request.node.name == 'test_LOG_14_forgot_password':
            page.RESET_EMAIL = (By.CSS_SELECTOR, "input[name='address'], input[name='email']")
            page.CAPTCHA = (By.CSS_SELECTOR, page.CAPTCHA[1] +
                            ", iframe[src*='challenges.cloudflare.com'], iframe[title*='Cloudflare']")
    if request.node.name in ('test_LOG_09_case_sensitivity', 'test_LOG_12_logout_and_back'):
        page.targeted_session_debug = True
    request.node.log_page = page
    page.debug_test_name = request.node.name
    try:
        page.load()
    except WebDriverException as exc:
        if "net::ERR_" in str(exc):
            raise RuntimeError("Target website unavailable from this environment") from exc
        raise
    challenge_guard(page)
    return page


def challenge_guard(page):
    if page.challenge():
        pytest.skip("Visible CAPTCHA/OTP requires manual completion; no bypass")


def assert_logged_in(page):
    outcome = page.wait_login_outcome()
    challenge_guard(page)
    # A completed redirect may expose only an account navigation link.
    # Save rejection before navigation can erase the application error.
    save_log01_evidence(page, "login-result")
    assert outcome != "credential-rejection", (
        "Observed credential rejection on login form; verify account/phone binding and data")
    assert outcome != "client-validation", "Login blocked by native field validation"
    # Generic alerts must not prevent an independent protected-page probe.
    verified = page.verify_account_session()
    challenge_guard(page)
    assert verified, (
        "No authenticated proof on protected account; outcome=" + outcome +
        "; website rejection is NOT established by a home redirect or generic alert")
    save_log01_evidence(page, "verified-account")


def assert_rejected(page, fields=(), allow_protection=False):
    page.wait_result(fields)
    challenge_guard(page)
    assert not page.authenticated(), "Invalid credentials authenticated"
    assert page.displayed(page.IDENTITY_INPUT), "Login form disappeared on rejection"
    assert page.errors(fields), "No visible application/native validation error"
    if not fields:
        # A format/required error must not masquerade as a credential rejection.
        assert not page.native_invalid(page.IDENTITY_INPUT), "Identity failed client validation"
        assert not page.native_invalid(page.PASSWORD_INPUT), "Password failed client validation"
        protected = page.message_matches(page.errors(), (
            "too many", "locked", "try again later", "rate limit",
            "qua nhieu", "khoa", "thu lai sau"))
        assert allow_protection or not protected, "Protection blocked credential verification"
        assert page.credential_errors() or (allow_protection and protected), (
            "No credential/protection rejection evidence")


def assert_required(page, fields):
    from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
    from selenium.webdriver.common.keys import Keys
    import json

    names = tuple("identity" if field == page.IDENTITY_INPUT else "password"
                  for field in fields)
    state = {}
    reason = "Required-field feedback not observed"
    try:
        state = page.required_validation()
        assert all(state[name].get("empty") for name in names), "Expected field is not empty"
        assert not page.authenticated(), "Session already authenticated before submission"
        # Real focus/blur triggers JS validators; never inject validity or submit JS.
        for field in fields:
            element = page.visible(field)
            element.click()
            element.send_keys(Keys.TAB)
        page.submit()

        def outcome(_):
            nonlocal state
            try:
                state = page.required_validation()
                return (page.required_feedback(state, names) or state["challenge"] or
                        page.authenticated())
            except StaleElementReferenceException:
                return False  # Reacquire the rendered inputs on the next poll.

        # Client validation is an outcome; no server response is required.
        page.wait.until(outcome)
        assert page.required_feedback(state, names), (
            "No required feedback for the missing field(s); CAPTCHA/disabled is insufficient")
        assert not page.authenticated(), "Blank credentials authenticated"
        assert all(page.displayed(field) for field in
                   (page.IDENTITY_INPUT, page.PASSWORD_INPUT, page.SUBMIT_BTN)), (
            "Login form disappeared; unauthenticated rejection is unconfirmed")
        assert not (page.displayed(page.AUTHENTICATED) or page.displayed(page.LOGOUT)), (
            "Authenticated controls visible after blank submission")
    except (AssertionError, TimeoutException, WebDriverException) as exc:
        reason = str(exc).split("Stacktrace:")[0].strip() or type(exc).__name__
        # Only validation metadata/text; redact values even if JS echoes credentials.
        try:
            state = page.required_validation()
        except WebDriverException:
            pass
        payload = json.dumps({"expected_empty": names, "validation": state,
                              "reason": reason}, ensure_ascii=False)
        secrets = [el.get_attribute("value") for locator in
                   (page.IDENTITY_INPUT, page.PASSWORD_INPUT)
                   for el in page.displayed(locator)]
        secrets += [value for key, value in os.environ.items() if any(
            word in key.upper() for word in ("PASSWORD", "EMAIL", "PHONE", "TOKEN", "SECRET"))]
        for value in sorted(filter(None, secrets), key=len, reverse=True):
            payload = payload.replace(value, "[REDACTED]")
        pytest.fail("LOG required validation DEBUG: " + payload, pytrace=False)


@pytest.mark.smoke
def test_LOG_01_email(request):
    email, password = credentials()
    page = page_of(request)
    try:
        page.login(email, password)
        assert page.authenticated(timeout=config.DEFAULT_TIMEOUT), (
            "Login did not expose authenticated account controls; "
            "credentials may be rejected or the deployed locator is unverified. "
            "See results/log01_debug; a home-page redirect is insufficient.")
        challenge_guard(page)
        page.open_account()
        assert page.authenticated(timeout=config.DEFAULT_TIMEOUT), (
            "Protected account did not expose authenticated controls; "
            "see results/log01_debug")
    except Exception:
        save_log01_evidence(page)
        raise


def save_log01_evidence(page, stage="LOG-01"):
    """Allowlisted DOM metadata only; never persist input values or session data."""
    import json
    from datetime import datetime
    from pathlib import Path
    from urllib.parse import urlsplit

    folder = Path(__file__).resolve().parents[1] / "results" / (
        "log01_debug" if stage == "LOG-01" else "log_session_fix")
    stem = getattr(page, "debug_test_name", "LOG") + "_" + stage + datetime.now().strftime("_%Y%m%d_%H%M%S_%f")
    evidence = {"authenticated_locator": list(page.AUTHENTICATED),
                "authentication": dict(page.auth_debug)}
    try:
        folder.mkdir(parents=True, exist_ok=True)
        url = urlsplit(page.driver.current_url)
        evidence["url"] = url.scheme + "://" + (url.hostname or "") + url.path
        evidence["has_errors"] = bool(page.errors())
        # Keep known validation wording only; never arbitrary server/DOM text.
        messages = page.errors((page.IDENTITY_INPUT, page.PASSWORD_INPUT))
        safe_messages = ("kh\u00f4ng \u0111\u00fang", "kh\u00f4ng t\u1ed3n t\u1ea1i", "kh\u00f4ng h\u1ee3p l\u1ec7", "kh\u00f4ng ch\u00ednh x\u00e1c",
                         "incorrect", "invalid", "required", "email", "s\u1ed1 \u0111i\u1ec7n tho\u1ea1i")
        evidence["error_categories"] = sorted({word for word in safe_messages
                                               if any(word in m.casefold() for m in messages)})
        evidence["error_count"] = len(messages)
        evidence["login_form_visible"] = bool(page.displayed(page.SUBMIT_BTN))
        evidence["authenticated_controls_visible"] = bool(
            page.displayed(page.AUTHENTICATED) or page.displayed(page.LOGOUT))
        evidence["popup_visible"] = bool(page.displayed(page.CLUB_POPUP))
        evidence["locators"] = {name: list(getattr(page, name)) for name in
                                ("CLUB_POPUP", "CLUB_GREETING", "CLUB_DISMISS", "LOGOUT", "ACCOUNT_LINK")}
        evidence["visible_locator_matches"] = [name for name in
            ("AUTHENTICATED", "LOGOUT", "ACCOUNT_LINK", "CLUB_POPUP", "SUBMIT_BTN")
            if page.displayed(getattr(page, name))]
        evidence["challenge"] = page.challenge()
        if getattr(page, 'failed_log_debug', False):
            evidence['stage'] = stage
            evidence['form_dom'] = page.driver.execute_script("""
                return [...document.querySelectorAll('form input, form button, form svg, input[name="password"] ~ *')]
                    .map(e => ({tag:e.tagName, type:e.getAttribute('type'),
                        name:e.getAttribute('name'), classes:e.getAttribute('class'),
                        visible:!!e.getClientRects().length}));
            """)
        evidence["elements"] = page.driver.execute_script("""
            return Array.from(document.querySelectorAll(
                'header a, header button, a[href*="account"], a[href*="logout"]'
            )).map(e => ({tag: e.tagName,
                visible: !!(e.getClientRects().length &&
                    getComputedStyle(e).visibility !== 'hidden'),
                path: e.tagName === 'A' ? new URL(e.href, location.href).pathname : null,
                has_text: !!String(e.innerText ?? e.textContent ?? '').trim()}));
        """)
        # Mask all input values in screenshots, including password reveal controls.
        page.driver.execute_script("""
            const mask = document.createElement('style');
            mask.id = 'log01-private-text-mask';
            mask.textContent = '* {color: transparent !important; text-shadow: none !important;} input, textarea, img {visibility: hidden !important;}';
            document.head.appendChild(mask);
            document.querySelectorAll('input, textarea').forEach(e => {
                e.dataset.log01OldVisibility = e.style.visibility;
                e.style.visibility = 'hidden';
            });
        """)
        try:
            page.driver.save_screenshot(str(folder / (stem + ".png")))
        finally:
            page.driver.execute_script("""
                document.getElementById('log01-private-text-mask')?.remove();
                document.querySelectorAll('[data-log01-old-visibility]').forEach(e => {
                    e.style.visibility = e.dataset.log01OldVisibility;
                    delete e.dataset.log01OldVisibility;
                });
            """)
    except Exception as exc:
        evidence["capture_error"] = type(exc).__name__
    payload = json.dumps(evidence, ensure_ascii=False, indent=2)
    for key, value in os.environ.items():
        if value and any(word in key.upper() for word in
                         ("PASSWORD", "EMAIL", "PHONE", "TOKEN", "SECRET", "COOKIE")):
            payload = payload.replace(value, "[REDACTED]")
    try:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / (stem + ".json")).write_text(payload, encoding="utf-8")
    except OSError as exc:
        import warnings
        warnings.warn("LOG evidence write failed: " + type(exc).__name__, RuntimeWarning)



def test_LOG_02_phone(request):
    phone, password = required("TEST_PHONE"), required("TEST_PASSWORD")
    page = page_of(request)
    page.login(phone, password)
    assert_logged_in(page)


def test_LOG_03_wrong_password(request):
    email, password = credentials()
    page = page_of(request)
    page.login(email, wrong_password(password))
    assert_rejected(page)


def test_LOG_04_unknown_account(request):
    email, password = required("LOG_NONEXISTENT_EMAIL"), required("TEST_PASSWORD")
    page = page_of(request)
    page.login(email, password)
    assert_rejected(page)


def test_LOG_05_both_empty(request):
    page = page_of(request)
    assert_required(page, (page.IDENTITY_INPUT, page.PASSWORD_INPUT))


def test_LOG_06_empty_password(request):
    email = required("TEST_EMAIL")
    page = page_of(request)
    page.type(page.IDENTITY_INPUT, email)
    assert_required(page, (page.PASSWORD_INPUT,))


def test_LOG_07_empty_identity(request):
    password = required("TEST_PASSWORD")
    page = page_of(request)
    page.type(page.PASSWORD_INPUT, password)
    assert_required(page, (page.IDENTITY_INPUT,))


@pytest.mark.parametrize("identity_case", [
    pytest.param("abc", id="abc"),
    pytest.param("abc@", id="abc-at"),
    pytest.param("@example.com", id="missing-local-part"),
    pytest.param("a b@example.com", id="internal-space"),
    pytest.param(None, id="valid-email-surrounding-spaces"),
])
def test_LOG_08_email_format_and_spaces(request, identity_case):
    from selenium.webdriver.common.keys import Keys

    def snapshot():
        # LOG-08 only: preserve visible wording before account probing navigates.
        state = page.required_validation()
        messages = list(dict.fromkeys(page.field_errors(page.IDENTITY_INPUT) +
                                     state["identity"]["messages"] + state["messages"]))
        # Include portal alerts outside the form; wording is diagnostic only.
        messages += page.driver.execute_script("""
            return [...document.querySelectorAll('[role="alert"], [data-sonner-toast], [data-state="open"][role="status"]')]
                .filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
                .map(e => String(e.innerText ?? e.textContent ?? '').trim()).filter(Boolean);
        """)
        secrets = [v for k, v in os.environ.items() if v and any(
            word in k.upper() for word in ("EMAIL", "PASSWORD", "PHONE", "TOKEN", "SECRET"))]
        for secret in sorted(secrets, key=len, reverse=True):
            messages = [m.replace(secret, "[REDACTED]") for m in messages]
        inputs = page.displayed(page.IDENTITY_INPUT)
        return {"messages": list(dict.fromkeys(messages)),
                "identity_metadata": ({key: inputs[0].get_attribute(key) for key in
                    ("name", "type", "pattern", "inputmode", "aria-invalid")} if inputs else {}),
                "native_validity": state["identity"].get("validity"),
                "challenge": state["challenge"],
                "submit_enabled": state["submit_enabled"]}

    password = required("TEST_PASSWORD")
    # Only the positive branch needs a real account email from .env.
    email = required("TEST_EMAIL") if identity_case is None else None
    if identity_case is None:
        assert email and "@" in email and not any(c.isspace() for c in email), (
            "TEST_EMAIL must be a valid test account email")
    page = page_of(request)
    if identity_case is not None:
        page.fill(identity_case, password)
        page.visible(page.IDENTITY_INPUT).send_keys(Keys.TAB)
        page.submit()
        save_log01_evidence(page, "format")

        def format_feedback():
            state = page.required_validation()["identity"]
            validity = state.get("validity", {})
            native = (state.get("willValidate") and
                      (validity.get("typeMismatch") or validity.get("patternMismatch"))
                      and state.get("validationMessage"))
            messages = page.field_errors(page.IDENTITY_INPUT) + state["messages"]
            # Field-associated format wording only; generic credential errors,
            # permanent hints and disabled buttons do not establish rejection.
            inline = page.message_matches(messages, (
                "email khong hop le", "email khong dung dinh dang",
                "email sai dinh dang", "dinh dang email", "invalid email",
                "valid email", "email is invalid", "email format"))
            if identity_case == "abc":
                # Shared Email/phone field: require explicit format wording,
                # including form/portal validation captured in the live evidence.
                shared_format = page.message_matches(snapshot()["messages"], (
                    "nhap email/s\u0111t hop le", "nhap email/sdt hop le",
                    "email/s\u0111t khong hop le", "email/sdt khong hop le",
                    "so dien thoai khong hop le", "so dien thoai sai dinh dang",
                    "dinh dang so dien thoai", "invalid phone number",
                    "valid phone number", "invalid email or phone",
                    "valid email or phone"))
                return bool(native or inline or shared_format)
            return bool(native or inline)

        if identity_case == "abc":
            # Preserve strict format semantics while recording otherwise missed
            # form-wide messages. No arbitrary error can satisfy this assertion.
            from selenium.common.exceptions import TimeoutException
            try:
                page.wait.until(lambda _: format_feedback() or page.challenge() or
                                page.authenticated(),
                                message="LOG-08: no Email/phone-format validation for 'abc'")
            except TimeoutException:
                state = page.required_validation()
                messages = (page.field_errors(page.IDENTITY_INPUT) +
                            state["identity"]["messages"] + state["messages"])
                unknown = page.message_matches(messages, (
                    "khong ton tai", "khong tim thay", "not found", "does not exist"))
                observed = snapshot()
                unknown = page.message_matches(observed["messages"], (
                    "khong ton tai", "khong tim thay", "not found", "does not exist"))
                # Record redacted wording and metadata, never input values.
                import json
                from pathlib import Path
                debug = {"case": "abc", "format_feedback": format_feedback(),
                         "unknown_identity_feedback": unknown,
                         "authenticated": page.authenticated(),
                         "login_form_visible": bool(page.displayed(page.IDENTITY_INPUT)),
                         "native_validity": state["identity"].get("validity"),
                         "message_count": len(messages), "observed": observed}
                folder = Path(__file__).resolve().parents[1] / "results" / "log08_debug"
                folder.mkdir(parents=True, exist_ok=True)
                (folder / "abc_classification.json").write_text(
                    json.dumps(debug, indent=2), encoding="utf-8")
                assert not debug["authenticated"], "Malformed identity authenticated"
                pytest.fail(
                    "LOG-08 abc: expected Email/phone-format rejection; " +
                    ("observed unknown-identity wording (not format validation)" if unknown else
                     "format rejection unconfirmed; inspect live inline/form error and locator") +
                    "; authenticated=False; see results/log08_debug/abc_classification.json",
                    pytrace=False)
        else:
            page.wait.until(lambda _: format_feedback() or page.challenge() or
                            page.authenticated(),
                            message="LOG-08: no email-format validation for " + repr(identity_case))
        challenge_guard(page)
        assert format_feedback(), "Malformed email has no field-specific format rejection"
        assert not page.authenticated(), "Malformed identity authenticated"
        assert page.displayed(page.IDENTITY_INPUT), "Rejection removed login form"
        return

    from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
    from selenium.webdriver.support.ui import WebDriverWait
    from utils.driver_factory import create_driver
    import json
    from pathlib import Path

    folder = Path(__file__).resolve().parents[1] / "results" / "log08_debug"
    debug = {"baseline_authenticated": False, "padded_login_authenticated": False,
             "classification": "unresolved", "phase": "baseline"}
    independent = None

    def verify_session():
        # Same proof and protected-page check as LOG-01; no duplicate outcome wait.
        assert page.authenticated(timeout=config.DEFAULT_TIMEOUT), (
            "LOG-08: no authenticated proof before account probe")
        challenge_guard(page)
        page.open_account()
        assert page.authenticated(timeout=config.DEFAULT_TIMEOUT), (
            "LOG-08: no authenticated proof on protected account")
        challenge_guard(page)

    def record_value(stage):
        inputs = page.displayed(page.IDENTITY_INPUT)
        current = inputs[0].get_property("value") if inputs else None
        debug[stage] = {"visible": bool(inputs), "is_padded": current == padded_email,
                        "is_trimmed": current == email}
        if inputs:
            assert current in (email, padded_email), "Identity changed beyond boundary trim"

    def format_rejection():
        state = page.required_validation()["identity"]
        validity = state.get("validity", {})
        native = (state.get("willValidate") and
                  (validity.get("typeMismatch") or validity.get("patternMismatch"))
                  and state.get("validationMessage"))
        inline = page.message_matches(page.field_errors(page.IDENTITY_INPUT) +
                                      state["messages"], (
            "email khong hop le", "email khong dung dinh dang", "email sai dinh dang",
            "dinh dang email", "invalid email", "valid email", "email is invalid", "email format"))
        return bool(native or inline)

    try:
        page.login(email, password)
        verify_session()
        debug["baseline_authenticated"] = True
        save_log01_evidence(page, "LOG-08-baseline-verified")

        # A new WebDriver has an independent cookie/storage session.
        debug["phase"] = "independent-session"
        independent = create_driver()
        page = LoginPage(independent)
        page.failed_log_debug = True
        page.debug_test_name = request.node.name
        page.wait = WebDriverWait(independent, config.DEFAULT_TIMEOUT,
                                 ignored_exceptions=(StaleElementReferenceException,))
        request.node.log_driver = independent
        request.node.log_page = page
        page.load()
        challenge_guard(page)
        assert not page.authenticated(), "Fresh browser unexpectedly authenticated"
        debug["independent_session"] = True
        debug["phase"] = "padded-login"
        padded_email = "  " + email + "  "
        page.type(page.IDENTITY_INPUT, padded_email)  # Selenium sends unchanged input.
        debug["padded_input_sent_unchanged"] = True
        record_value("before_blur")
        page.visible(page.IDENTITY_INPUT).send_keys(Keys.TAB)
        record_value("after_blur")
        page.type(page.PASSWORD_INPUT, password)
        debug["submit_clicked"] = page.submit()
        record_value("after_submit")

        def outcome(_):
            if page.challenge():
                return "captcha"
            if format_rejection():
                return "format-rejection"
            if page.credential_errors():
                return "website-credential-rejection"
            if page.authenticated():
                return "authenticated"
            # Permit the LOG-01 protected-page probe after a completed redirect.
            if not page.displayed(page.SUBMIT_BTN) and page.displayed(page.ACCOUNT_LINK):
                return "account-probe-needed"
            return False

        result = page.wait.until(outcome, message="LOG-08: padded login outcome unresolved")
        debug["outcome"] = result
        record_value("after_result")
        debug["observed_before_account_probe"] = snapshot()
        challenge_guard(page)
        if result == "format-rejection":
            assert format_rejection(), "Email-format evidence disappeared"
            assert page.displayed(page.IDENTITY_INPUT), "Format rejection removed login form"
            assert not page.authenticated(), "Format rejection also authenticated"
            debug["classification"] = "website-format-rejection"
        else:
            assert result != "website-credential-rejection", (
                "LOG-08 website rejected padded credentials although baseline succeeded")
            verify_session()
            debug["padded_login_authenticated"] = True
            debug["classification"] = "authenticated-boundary-spaces-accepted"
            save_log01_evidence(page, "LOG-08-verified-account")
    except pytest.skip.Exception:
        debug["classification"] = "captcha-or-prerequisite-manual-required"
        raise
    except OSError:
        debug["classification"] = "infrastructure-error"
        raise
    except TimeoutException:
        debug["classification"] = "timeout-unresolved"
        raise
    except AssertionError:
        debug["classification"] = ("website-credential-rejection" if
            debug.get("outcome") == "website-credential-rejection" else "assertion-unconfirmed")
        raise
    except WebDriverException:
        debug["classification"] = "selenium-infrastructure-error"
        raise
    finally:
        if debug.get("outcome") == "captcha":
            debug["classification"] = "captcha-manual-required"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "spaces_classification.json").write_text(
                json.dumps(debug, indent=2), encoding="utf-8")
            if independent is not None:
                save_log01_evidence(page, "LOG-08-final")
        except (OSError, WebDriverException) as exc:
            request.node.add_report_section("call", "LOG-08 evidence", type(exc).__name__)
        finally:
            if independent is not None:
                try:
                    independent.quit()
                except WebDriverException:
                    request.node.add_report_section("call", "LOG-08 cleanup", "Driver quit failed")
                request.node.log_driver = request.getfixturevalue("login_driver")
                request.node.log_page = None


def test_LOG_09_case_sensitivity(request):
    email, password = credentials()
    if email.upper() == email:
        pytest.skip("Email must contain lowercase letters to test uppercase login")
    page = page_of(request)
    uppercase_email = email.upper()  # Send uppercase unchanged; never lowercase in test code.
    page.fill(uppercase_email, password)
    assert page.visible(page.IDENTITY_INPUT).get_property("value") == uppercase_email, (
        "Website changed uppercase email before submission")
    page.auth_debug["uppercase_input_verified"] = True
    page.submit()
    assert_logged_in(page)


def test_LOG_09_password_case_sensitivity(request):
    email, password = credentials()
    if password.swapcase() == password:
        pytest.skip("Password must contain letters to test case sensitivity")
    page = page_of(request)
    # Positive baseline prevents a disabled/unusable account from passing this branch.
    page.login(email, password)
    assert_logged_in(page)
    page.logout()
    challenge_guard(page)
    page.load()
    challenge_guard(page)
    assert page.displayed(page.IDENTITY_INPUT), "Baseline session did not log out"
    assert not page.authenticated(), "Baseline session remains authenticated"
    page.login(email, password.swapcase())
    assert_rejected(page)


def test_LOG_10_five_failures_protection(request):
    # Dedicated disposable account avoids locking the positive-test account.
    email = required("LOG_LOCKOUT_EMAIL")
    password = required("LOG_LOCKOUT_PASSWORD")
    if email.casefold() == os.getenv("TEST_EMAIL", "").casefold():
        pytest.skip("LOG_LOCKOUT_EMAIL must differ from the main test account")
    page = page_of(request)
    protection_words = ("too many", "locked", "try again later", "rate limit",
                        "qua nhieu", "khoa", "thu lai sau")
    import unicodedata
    for attempt in range(5):
        page.load()
        challenge_guard(page)
        page.login(email, wrong_password(password))
        page.wait_result()
        # A challenge during attempts 1-4 is protection, but does not prove 5 attempts.
        if page.challenge() and attempt < 4:
            pytest.skip("Protection activated before five attempts; manual CAPTCHA needed")
        if not page.challenge():
            assert_rejected(page, allow_protection=True)
            response = " ".join(page.errors()).lower()
            response = "".join(c for c in unicodedata.normalize("NFD", response)
                               if not unicodedata.combining(c))
            if attempt < 4 and any(word in response for word in protection_words):
                pytest.skip("Rate limit/lockout before five attempts; stopped for account safety")
    text = " ".join(page.errors()).lower()
    text = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    assert page.challenge() or any(word in text for word in protection_words), (
        "Five incorrect submissions produced no visible lockout/rate limit/CAPTCHA evidence")
    assert not page.authenticated()


def test_LOG_11_password_visibility(request):
    password = required("TEST_PASSWORD")
    page = page_of(request)
    page.type(page.PASSWORD_INPUT, password)
    assert page.visible(page.PASSWORD_INPUT).get_attribute("type") == "password"
    for expected in ("text", "password"):
        page.toggle_password()
        page.wait.until(lambda _: page.visible(page.PASSWORD_INPUT).get_attribute("type") == expected)
        assert page.visible(page.PASSWORD_INPUT).get_attribute("value") == password


@pytest.mark.skip(reason="Manual Testing")
def test_LOG_12_logout_and_back(request):
    email, password = credentials()
    page = page_of(request)
    page.login(email, password)
    assert_logged_in(page)
    page.dismiss_post_login_popups()
    save_log01_evidence(page, "before-logout")
    page.logout()
    challenge_guard(page)
    assert not page.authenticated(), "Logout left protected account accessible"
    page.driver.back()
    page.wait.until(lambda _: page.driver.execute_script("return document.readyState") == "complete")
    assert not page.authenticated(), "Back restored authenticated controls after logout"
    page.driver.refresh()
    page.open_account()
    page.wait.until(lambda _: page.challenge() or page.displayed(page.IDENTITY_INPUT) or page.authenticated())
    challenge_guard(page)
    assert not page.authenticated(), "Protected account remains accessible after logout"
    assert page.displayed(page.IDENTITY_INPUT), "Protected account did not require login"
    assert page.displayed(page.PASSWORD_INPUT) and page.displayed(page.SUBMIT_BTN), (
        "Protected account did not expose the complete login form")
    save_log01_evidence(page, "after-back-protected-denied")


def test_LOG_13_session_reload_and_tab(request):
    email, password = credentials()
    page = page_of(request)
    page.login(email, password)
    assert_logged_in(page)
    page.driver.refresh()
    page.wait.until(lambda _: page.challenge() or page.authenticated())
    challenge_guard(page)
    assert page.authenticated(), "Reload lost session"
    original = page.driver.current_window_handle
    page.driver.switch_to.new_window("tab")
    try:
        page.open_account()
        page.wait.until(lambda _: page.challenge() or page.authenticated() or page.displayed(page.IDENTITY_INPUT))
        challenge_guard(page)
        assert page.authenticated(), "New tab lost session"
    finally:
        page.driver.close()
        page.driver.switch_to.window(original)


@pytest.mark.skip(reason="Manual Testing")
def test_LOG_14_forgot_password(request):
    email = required("TEST_EMAIL")
    unknown = required("LOG_NONEXISTENT_EMAIL")
    assert email.casefold() != unknown.casefold(), "Recovery accounts must be distinct"
    page = page_of(request)
    # Empty input must be rejected, not counted as successful recovery.
    page.open_reset()
    challenge_guard(page)
    field = page.visible(page.RESET_EMAIL)
    assert field.get_attribute("value") == ""
    if page.visible(page.RESET_SUBMIT).is_enabled():
        page.submit(page.RESET_SUBMIT)
        page.wait.until(lambda _: page.challenge() or page.required_error(page.RESET_EMAIL))
        challenge_guard(page)
        assert page.required_error(page.RESET_EMAIL), "Empty recovery email accepted"
    save_log01_evidence(page, 'reset-empty')
    assert page.required_error(page.RESET_EMAIL), "No required validation for empty recovery email"
    for identity in (email, unknown):
        page.open_reset()
        challenge_guard(page)
        page.type(page.RESET_EMAIL, identity)
        assert page.submit(page.RESET_SUBMIT), "Recovery submit is disabled; request not sent"
        page.wait.until(lambda _: page.challenge() or page.reset_messages() or
                        page.errors((page.RESET_EMAIL,)) or page.field_errors(page.RESET_EMAIL))
        challenge_guard(page)
        save_log01_evidence(page, 'reset-known' if identity == email else 'reset-unknown')
        from urllib.parse import urlsplit
        assert urlsplit(page.driver.current_url).path != '/login', 'Recovery returned to login without acknowledgement'
        messages = " ".join(page.reset_messages())
        if identity == email:
            assert messages, "Valid recovery email has no success acknowledgement"
        else:
            # Generic success prevents account enumeration; explicit unknown-email error also valid.
            assert messages or page.message_matches(page.errors((page.RESET_EMAIL,)) + page.field_errors(page.RESET_EMAIL), (
                "khong ton tai", "khong tim thay", "not found", "does not exist")), (
                "Unknown email has no success acknowledgement or explicit unknown-account response")
        assert not page.authenticated(), "Password recovery unexpectedly authenticated account"
