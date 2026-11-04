"""Page Object: LoginPage - phụ trách: TV2 - module: LOG.
Quy tắc: locator đặt ở đầu lớp; method là hành động nghiệp vụ; KHÔNG assert trong page.
"""
from selenium.webdriver.common.by import By  # noqa: F401
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

from pages.base_page import BasePage


class LoginPage(BasePage):
    PATH = "/login"

    # TODO: khai báo locator, ví dụ  EMAIL_INPUT = (By.ID, "email")

    def load(self):
        import os
        from pages.register_page import RegisterPage
        self.open(os.getenv("LOG_LOGIN_PATH", self.PATH))
        RegisterPage(self.driver).accept_cookies()
        self.wait.until(lambda _: self.challenge() or self.displayed(self.IDENTITY_INPUT))
        if self.challenge():
            return self
        self.visible(self.IDENTITY_INPUT)
        self.visible(self.PASSWORD_INPUT)
        self.visible(self.SUBMIT_BTN)
        return self

    # LOG additions: selectors can be overridden after inspecting a target deployment.
    IDENTITY_INPUT = (By.CSS_SELECTOR, "input[name='email'], input[name='username'], input[name='phone']")
    PASSWORD_INPUT = (By.CSS_SELECTOR, "input[name='password']")
    SUBMIT_BTN = (By.CSS_SELECTOR, "button[ga-tracking-value='login_account'], form button[type='submit']")
    PASSWORD_TOGGLE = (By.CSS_SELECTOR, ".toggle-password, [data-action='toggle-password'], button[class*='password'], [aria-label*='m\u1eadt kh\u1ea9u']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error-message, .form-error, .text-red-500, .text-danger, [role='alert'], .alert-danger")
    AUTHENTICATED = (By.CSS_SELECTOR, "a[href*='logout'], button[data-action='logout']")
    # Observed in results/log01_debug/*.json; navigation cue, never session proof.
    ACCOUNT_LINK = (By.CSS_SELECTOR, "a[href='/account/info']")
    # UI-derived candidates, NOT yet verified against the live COOL CLUB DOM.
    CLUB_POPUP = (By.XPATH, "//*[.//*[normalize-space(.)='COOL CLUB' or normalize-space(.)='COOLCLUB'] and .//*[normalize-space(.)='Bỏ qua bước này'] and .//*[starts-with(normalize-space(.),'Hi ')]][not(.//*[.//*[normalize-space(.)='COOL CLUB' or normalize-space(.)='COOLCLUB'] and .//*[normalize-space(.)='Bỏ qua bước này'] and .//*[starts-with(normalize-space(.),'Hi ')]])]")
    CLUB_GREETING = (By.XPATH, ".//*[starts-with(normalize-space(.),'Hi ') and not(.//*[starts-with(normalize-space(.),'Hi ')])]")
    CLUB_DISMISS = (By.XPATH, ".//*[normalize-space(.)='Bỏ qua bước này' and not(.//*[normalize-space(.)='Bỏ qua bước này'])] | .//*[self::button or self::a][@aria-label='Close' or @aria-label='Đóng' or normalize-space(.)='×' or normalize-space(.)='X']")
    # Content-scoped candidates; live verification is blocked by network policy.
    PROFILE_SKIP = (By.XPATH, "//*[normalize-space(.)='B\u1ecf qua b\u01b0\u1edbc n\u00e0y' and not(.//*[normalize-space(.)='B\u1ecf qua b\u01b0\u1edbc n\u00e0y'])]")
    OFFER_POPUP = (By.XPATH,
        "//*[contains(normalize-space(.),'CoolCash') or normalize-space(.)='MUA S\u1eaeM NGAY']"
        "[not(.//*[contains(normalize-space(.),'CoolCash') or normalize-space(.)='MUA S\u1eaeM NGAY'])]"
        "/ancestor::*[@role='dialog' or @aria-modal='true' or "
        "contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'popup') or "
        "contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'modal')][1]")
    OFFER_CLOSE = (By.XPATH,
        ".//*[self::button or self::a or @role='button' or self::span or self::div]"
        "[@aria-label='Close' or @aria-label='\u0110\u00f3ng' or @title='Close' or @title='\u0110\u00f3ng' or "
        "normalize-space(.)='\u00d7' or normalize-space(.)='X' or normalize-space(.)='\u2715' or "
        "contains(concat(' ',normalize-space(@class),' '),' close ') or "
        "contains(@class,'popup-close') or contains(@class,'modal-close') or "
        "contains(@class,'popup__close') or contains(@class,'modal__close')]"
        "[not(contains(normalize-space(.),'MUA S\u1eaeM NGAY'))]")
    LOGOUT = (By.XPATH, "//*[self::a or self::button][contains(@href,'logout') or normalize-space(.)='\u0110\u0103ng xu\u1ea5t']")
    FORGOT_LINK = (By.XPATH, "//*[self::a or self::button][contains(normalize-space(.),'Qu\u00ean m\u1eadt kh\u1ea9u')]")
    RESET_EMAIL = (By.CSS_SELECTOR, "input[name='address'], input[name='email']")
    RESET_SUBMIT = (By.CSS_SELECTOR,
                    "form:has(input[name='address']) button:not([type='button']):not([type='reset']), "
                    "form:has(input[name='email']) button[type='submit']")
    RESET_SUCCESS = (By.CSS_SELECTOR, ".alert-success, .success-message, [role='status']")
    CAPTCHA = (By.CSS_SELECTOR, "iframe[src*='bframe'], iframe[title*='challenge'], .g-recaptcha, .h-captcha, input[name='otp']")

    def __init__(self, driver):
        super().__init__(driver)
        self._greeting_document = None
        self.auth_debug = {"popup_seen": False, "personalized_greeting": False,
                           "popup_closed": False, "matched_locators": [],
                           "popup_locators_live_verified": False}
        import os
        for name in ("IDENTITY_INPUT", "PASSWORD_INPUT", "SUBMIT_BTN", "PASSWORD_TOGGLE",
                     "ERROR_MESSAGE", "AUTHENTICATED", "RESET_EMAIL", "RESET_SUBMIT", "RESET_SUCCESS",
                     "CLUB_POPUP", "CLUB_GREETING", "CLUB_DISMISS", "ACCOUNT_LINK", "LOGOUT",
                     "PROFILE_SKIP", "OFFER_POPUP", "OFFER_CLOSE"):
            selector = os.getenv("LOG_" + name + "_CSS")
            if selector:
                setattr(self, name, (By.CSS_SELECTOR, selector))

    def displayed(self, locator):
        try:
            return [el for el in self.driver.find_elements(*locator) if el.is_displayed()]
        except StaleElementReferenceException:
            return []

    def visible(self, locator):
        # Responsive pages may contain a hidden copy before the active form.
        return self.wait.until(lambda _: next(iter(self.displayed(locator)), False))

    def clickable(self, locator):
        # LOG-only override: responsive hidden copies must not win the lookup.
        return self.wait.until(lambda _: next((el for el in self.displayed(locator)
                                               if el.is_enabled()), False))

    def native_invalid(self, locator, flag=None):
        return any(self.driver.execute_script(
            "return arguments[1] ? !!arguments[0].validity[arguments[1]] : "
            "!arguments[0].validity.valid;", el, flag)
            for el in self.displayed(locator))

    @staticmethod
    def message_matches(messages, words):
        import unicodedata
        text = unicodedata.normalize("NFD", " ".join(messages).casefold())
        text = "".join(c for c in text if not unicodedata.combining(c))
        return any(word in text for word in words)

    def credential_errors(self):
        # A generic alert on the home page is not a credential rejection.
        if not (self.displayed(self.IDENTITY_INPUT) and self.displayed(self.PASSWORD_INPUT)):
            return []
        messages = self.errors((self.IDENTITY_INPUT, self.PASSWORD_INPUT))
        return messages if self.message_matches(messages, (
            "khong chinh xac", "khong dung", "khong ton tai", "incorrect",
            "invalid credentials", "wrong password", "account not found")) else []

    def required_error(self, locator):
        return self.native_invalid(locator, "valueMissing") or self.message_matches(
            self.field_errors(locator), ("bat buoc", "required", "khong duoc de trong",
                                         "vui long nhap", "please enter"))

    def wait_login_outcome(self):
        # Wait through redirects/popups; never stop at a public account link.
        def outcome(_):
            if self.challenge():
                return "challenge"
            if self.authenticated():
                return "authenticated"
            if self.credential_errors():
                return "credential-rejection"
            if any(self.native_invalid(field) for field in
                   (self.IDENTITY_INPUT, self.PASSWORD_INPUT)):
                return "client-validation"
            return False
        try:
            return self.wait.until(outcome)
        except TimeoutException:
            return "unresolved"

    def handle_post_login_popup(self):
        """Record only a boolean greeting proof, dismiss, and wait for disappearance.

        Called by authentication polling; absence of a popup is not an error.
        No username or profile values are retained.
        """
        popups = self.displayed(self.CLUB_POPUP)
        if not popups:
            return False
        self.auth_debug["popup_seen"] = True
        popup = popups[0]

        def personalized(_):
            roots = self.displayed(self.CLUB_POPUP) if getattr(
                self, 'targeted_session_debug', False) else [popup]
            for el in [el for root in roots for el in root.find_elements(*self.CLUB_GREETING)]:
                text = " ".join(el.text.split())
                if el.is_displayed() and re.fullmatch(r"Hi\s+[^\[\]{}<>\n]+", text):
                    name = text[3:].strip(" ,!:.")
                    if name and name.casefold() not in ("bạn", "guest", "customer", "user"):
                        return True
            return False

        self.wait.until(personalized)
        self.auth_debug["personalized_greeting"] = True
        self.auth_debug["matched_locators"] = ["CLUB_POPUP", "CLUB_GREETING"]
        document = self.driver.find_element(By.TAG_NAME, "html")
        self._greeting_document = document
        def dismiss_button(_):
            roots = self.displayed(self.CLUB_POPUP) if getattr(
                self, 'targeted_session_debug', False) else [popup]
            return next((el for root in roots for el in root.find_elements(
                *self.CLUB_DISMISS) if el.is_displayed() and el.is_enabled()), False)
        button = self.wait.until(dismiss_button)
        button.click()
        if getattr(self, 'targeted_session_debug', False):
            self.wait.until(lambda _: not self.displayed(self.CLUB_POPUP))
        else:
            self.wait.until(EC.invisibility_of_element(popup))
        self.auth_debug["popup_closed"] = True
        self.auth_debug["matched_locators"].append("CLUB_DISMISS")
        # Proof is valid only in this document, never across navigation/logout.
        self._greeting_document = document
        return True

    def dismiss_post_login_popups(self, timeout=3):
        """Shared cleanup after session proof; missing optional popups are normal.

        Wait separately for each stage because the offer can appear after skipping
        the profile. A popup that is found must close successfully.
        """
        wait = WebDriverWait(self.driver, timeout)
        try:
            skip = wait.until(lambda _: next(iter(self.displayed(self.PROFILE_SKIP)), False))
        except TimeoutException:
            skip = None
        if skip is not None:
            wait.until(EC.element_to_be_clickable(skip)).click()
            wait.until(EC.invisibility_of_element(skip))

        try:
            popup = wait.until(lambda _: next(iter(self.displayed(self.OFFER_POPUP)), False))
        except TimeoutException:
            return
        self.auth_debug["offer_popup_seen"] = True
        def current_close(_):
            roots = self.displayed(self.OFFER_POPUP) if getattr(
                self, 'failed_log_debug', False) else [popup]
            try:
                return next((el for root in roots for el in root.find_elements(
                    *self.OFFER_CLOSE) if el.is_displayed() and el.is_enabled()), False)
            except StaleElementReferenceException:
                if getattr(self, 'failed_log_debug', False):
                    return False
                raise
        close = wait.until(current_close)
        close.click()
        if getattr(self, 'failed_log_debug', False):
            wait.until(lambda _: not self.displayed(self.OFFER_POPUP))
        else:
            wait.until(EC.invisibility_of_element(popup))
        self.auth_debug["offer_popup_closed"] = True

    def _authentication_evidence(self):
        self.auth_debug["matched_locators"] = []
        # An email field on a profile is not a login form.
        if self.challenge() or (self.displayed(self.IDENTITY_INPUT)
                                and self.displayed(self.PASSWORD_INPUT)
                                and self.displayed(self.SUBMIT_BTN)):
            self._greeting_document = None
            return False
        if self.handle_post_login_popup():
            return True
        if self.displayed(self.AUTHENTICATED) or self.displayed(self.LOGOUT):
            self.auth_debug["matched_locators"] = [
                name for name in ("AUTHENTICATED", "LOGOUT")
                if self.displayed(getattr(self, name))]
            return True
        if self._greeting_document is not None:
            if not EC.staleness_of(self._greeting_document)(self.driver):
                return True
            self._greeting_document = None
        return False

    def verify_account_session(self):
        """Probe the protected page; a public account link alone proves nothing."""
        from utils import config
        if getattr(self, 'targeted_session_debug', False):
            self.wait.until(lambda _: not self.displayed(self.SUBMIT_BTN))
            self.dismiss_post_login_popups()
        self.open_account()
        return self.authenticated(timeout=config.DEFAULT_TIMEOUT)

    def authenticated(self, timeout=0):
        """Require personalized greeting or visible authenticated account controls.

        A redirect or account link alone never counts as authentication.
        With an explicit timeout, probe the protected page once if necessary.
        """
        if not timeout:
            try:
                verified = self._authentication_evidence()
            except TimeoutException:
                return False
            if verified:
                self.dismiss_post_login_popups()
            return verified
        try:
            # Explicit verification may follow the observed account link once.
            # Non-blocking polling never navigates (rejection/logout assertions).
            probed_account = False

            def evidence(_):
                nonlocal probed_account
                if self._authentication_evidence():
                    return True
                if (not probed_account and not self.challenge()
                        and not self.displayed(self.SUBMIT_BTN)
                        and not self.errors() and self.displayed(self.ACCOUNT_LINK)):
                    probed_account = True
                    self.open_account()
                return False

            verified = bool(WebDriverWait(self.driver, timeout).until(evidence))
        except TimeoutException:
            return False
        self.dismiss_post_login_popups()
        return verified

    def challenge(self):
        return bool(self.displayed(self.CAPTCHA))

    def fill(self, identity, password):
        self.type(self.IDENTITY_INPUT, identity)
        self.type(self.PASSWORD_INPUT, password)

    def submit(self, locator=None):
        button = self.visible(locator or self.SUBMIT_BTN)
        if button.is_enabled():
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
            button.click()
            return True
        return False

    def login(self, identity, password):
        self._greeting_document = None
        self.fill(identity, password)
        self.submit()

    def errors(self, fields=(), include_generic=True):
        messages = ([el.text.strip() for el in self.displayed(self.ERROR_MESSAGE) if el.text.strip()]
                    if include_generic else [])
        for locator in fields:
            for el in self.displayed(locator):
                message = el.get_property("validationMessage")
                if message:
                    messages.append(message)
                # aria-describedby may point to a permanent hint, not an error.
                invalid = el.get_attribute("aria-invalid") == "true" or bool(message)
                targets = (el.get_attribute("aria-errormessage") or "",
                           el.get_attribute("aria-describedby") or "") if invalid else ()
                for target in targets:
                    for element_id in target.split():
                        for error in self.displayed((By.ID, element_id)):
                            if error.text.strip():
                                messages.append(error.text.strip())
        return messages

    def field_errors(self, locator):
        """Return only validation evidence associated with the requested field."""
        messages = self.errors((locator,), include_generic=False)
        if getattr(self, 'failed_log_debug', False):
            for element in self.displayed(locator):
                messages += self.driver.execute_script("""
                    const e = arguments[0], messages = [];
                    for (let n = e.parentElement; n && n !== e.form &&
                         n !== document.body; n = n.parentElement) {
                        if ([...n.querySelectorAll('input')].some(x =>
                            x !== e && x.type !== 'hidden')) break;
                        for (const x of n.querySelectorAll('*'))
                            if (!x.children.length &&
                                !x.matches('input,button,label,script,style,svg,path') &&
                                x.getClientRects().length &&
                                getComputedStyle(x).visibility !== 'hidden') {
                                const text = String(x.innerText ?? x.textContent ?? '').trim();
                                if (text) messages.push(text);
                            }
                    }
                    return messages;
                """, element)
        return list(dict.fromkeys(messages))

    def required_validation(self):
        """Read client feedback for LOG-05/06/07 without changing other outcomes."""
        state = {}
        for name, locator in (("identity", self.IDENTITY_INPUT),
                              ("password", self.PASSWORD_INPUT)):
            elements = self.displayed(locator)
            if not elements:
                state[name] = {"visible": False, "messages": []}
                continue
            state[name] = self.driver.execute_script("""
                const e = arguments[0];
                const visible = n => !!n.getClientRects().length &&
                    getComputedStyle(n).visibility !== 'hidden';
                const messages = [];
                const add = n => {
                    // SVG/other non-HTMLElement nodes may have no innerText.
                    const text = String(n?.innerText ?? n?.textContent ?? '').trim();
                    if (n && visible(n) && text)
                        messages.push(text);
                };
                // Error references may be rendered without aria-invalid.
                for (const attr of ['aria-errormessage', 'aria-describedby'])
                    for (const id of (e.getAttribute(attr) || '').split(/\\s+/))
                        if (id) add(document.getElementById(id));
                // Stop before a container holding another input or the whole form.
                // Leaf text includes JS inline errors with no known CSS class.
                for (let n = e.parentElement; n && n !== e.form &&
                     n !== document.body; n = n.parentElement) {
                    if ([...n.querySelectorAll('input')].some(x => x !== e &&
                        !['hidden', 'checkbox', 'radio'].includes(x.type))) break;
                    for (const child of n.querySelectorAll('*'))
                        if ((!child.children.length || child.matches('[role="alert"]')) &&
                            !child.matches('input, button, script, style, label')) add(child);
                }
                return {visible: true, empty: e.value === '',
                    required: e.required, willValidate: e.willValidate,
                    validity: {valid: e.validity.valid,
                        valueMissing: e.validity.valueMissing,
                        customError: e.validity.customError,
                        typeMismatch: e.validity.typeMismatch,
                        patternMismatch: e.validity.patternMismatch},
                    ariaInvalid: e.getAttribute('aria-invalid'),
                    validationMessage: String(e.validationMessage ?? '').trim(),
                    messages: [...new Set(messages)]};
            """, elements[0])
        # JS can render a form-wide error without a standard error CSS class.
        form_messages = self.driver.execute_script("""
            const input = arguments[0];
            const root = input && (input.form || input.closest('[role="dialog"]'));
            return root ? [...root.querySelectorAll('*')].filter(n =>
                !n.children.length && !n.matches('input, button, label, script, style') &&
                n.getClientRects().length && getComputedStyle(n).visibility !== 'hidden'
            ).map(n => String(n.innerText ?? n.textContent ?? '').trim()).filter(Boolean) : [];
        """, next(iter(self.displayed(self.IDENTITY_INPUT)), None))
        state["messages"] = list(dict.fromkeys(self.errors() + form_messages))
        state["challenge"] = self.challenge()
        state["submit_enabled"] = any(e.is_enabled() for e in self.displayed(self.SUBMIT_BTN))
        return state

    def required_feedback(self, state, names):
        """Require missing-value semantics; aria-invalid/disabled alone are insufficient."""
        import unicodedata

        def normalized(text):
            text = unicodedata.normalize("NFD", text.casefold()).replace("\u0111", "d")
            return "".join(c for c in text if not unicodedata.combining(c))

        def required(text):
            return any(word in normalized(text) for word in (
                "bat buoc", "required", "khong duoc de trong", "khong de trong",
                "khong duoc bo trong", "vui long nhap", "please enter",
                "please fill", "must not be empty", "cannot be empty"))

        for name in names:
            field = state[name]
            if not field.get("visible") or not field.get("empty"):
                continue
            native = field.get("validity", {}).get("valueMissing", False)
            linked = any(required(m) for m in field["messages"] +
                         [field.get("validationMessage", "")])
            # A global message must name the missing field for LOG-06/07.
            named = any(required(m) and any(word in normalized(m) for word in
                        (("email", "dien thoai", "sdt", "tai khoan", "phone", "username")
                         if name == "identity" else ("mat khau", "password")))
                        for m in state["messages"])
            if native or linked or named:
                return True
        # LOG-05 permits one general required-information message.
        return len(names) == 2 and all(state[n].get("empty") for n in names) and any(
            required(m) for m in state["messages"])

    def wait_result(self, fields=(), success=None):
        fields = fields or (self.IDENTITY_INPUT, self.PASSWORD_INPUT)
        try:
            return self.wait.until(lambda _: self.challenge() or self.authenticated()
                                   or self.errors(fields)
                                   or (success and self.displayed(success)))
        except TimeoutException:
            raise TimeoutException(
                "No authentication, validation or challenge evidence before timeout; "
                "inspect LOG diagnostics and verify deployed locators") from None

    def logout(self):
        self._greeting_document = None
        if not self.displayed(self.LOGOUT):
            self.open_account()
        if getattr(self, 'failed_log_debug', False):
            from pages.register_page import RegisterPage
            RegisterPage(self.driver).accept_cookies()
            self.dismiss_post_login_popups()
            self.click_unobstructed(self.LOGOUT)
        else:
            self.visible(self.LOGOUT).click()
        self.wait.until(lambda _: self.driver.execute_script("return document.readyState") == "complete")
        self.wait.until(lambda _: not self.authenticated())
        # Keep history intact for LOG-12; protected access is checked after Back.

    def open_account(self):
        import os
        self._greeting_document = None
        default = "/account/info" if getattr(self, 'targeted_session_debug', False) else "/account"
        return self.open(os.getenv("LOG_ACCOUNT_PATH", default))

    def open_reset(self):
        self.load()
        self.click(self.FORGOT_LINK)
        self.wait.until(lambda _: self.challenge() or not self.displayed(self.PASSWORD_INPUT))
        if self.challenge():
            return self
        self.visible(self.RESET_EMAIL)
        self.visible(self.RESET_SUBMIT)
        return self

    def reset_messages(self):
        """Require recovery acknowledgement semantics, not arbitrary form text."""
        messages = [el.text.strip() for el in self.displayed(self.RESET_SUCCESS)]
        texts = self.driver.execute_script("""
            return [...document.querySelectorAll('main *, [role="dialog"] *')]
                .filter(e => !e.children.length && e.getClientRects().length &&
                    getComputedStyle(e).visibility !== 'hidden' &&
                    !e.matches('button,a,label,script,style,input'))
                .map(e => String(e.innerText ?? e.textContent ?? '').trim()).filter(Boolean);
        """)
        words = ("\u0111a gui", "gui thanh cong", "kiem tra email", "kiem tra hop thu",
                 "email has been sent", "check your email", "reset link sent")
        return list(dict.fromkeys(m for m in messages + texts
                                 if m and self.message_matches([m], words)))

    def click_unobstructed(self, locator):
        """Reacquire after render; wait for a real pointer click, never JS click."""
        from selenium.common.exceptions import ElementClickInterceptedException

        def click(_):
            try:
                element = self.clickable(locator)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", element)
                element.click()
                return True
            except (StaleElementReferenceException, ElementClickInterceptedException):
                return False
        self.wait.until(click)

    def toggle_password(self):
        # Scope fallback candidates to the password wrapper. Their behavior must
        # still satisfy LOG-11; a candidate match alone never proves success.
        candidates = self.displayed(self.PASSWORD_TOGGLE)
        locator = self.PASSWORD_TOGGLE if candidates else (By.XPATH,
            "//input[@name='password']/parent::*//*[self::button or @role='button' "
            "or contains(@class,'eye') or contains(@class,'toggle')]"
            " | //input[@name='password']/following-sibling::*[self::svg]")
        self.click_unobstructed(locator)
