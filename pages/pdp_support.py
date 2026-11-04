"""PDP-only implementation. Candidate CSS must be checked in the Windows DOM.

Optional PDP_LOCATORS_FILE maps locator names to CSS strings. No JS mutations.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from selenium.common.exceptions import (ElementClickInterceptedException,
                                       StaleElementReferenceException, TimeoutException, WebDriverException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class PDPDataUnavailable(ValueError):
    """Configured URL is not the requested product detail page."""


class ProductDetailsMixin:
    # Semantic selectors first; class fallbacks are unverified on the current site.
    LOCATORS = {
        "name": "main h1, h1.product-single__title, h1.product-title",
        "sku": "[itemprop='sku'], .product-single__sku, [data-testid='product-sku']",
        "price": "[itemprop='price'], [data-testid='product-price'], .product-single__price",
        "images": "#product-gallery img",
        "description": "#product-description, #description, [itemprop='description'], .product-description",
        "information": "#product-description [aria-label='Thông số sản phẩm'], [data-testid='product-information'], .product-single__description, .product-features",
        "colors": "#product-detail-variants a[href*='?color=']:has(img[alt^='color ']), [data-option='color'] button, [data-testid='color-option'], .option-color__item",
        "sizes": "[data-option='size'] button, [data-testid='size-option'], .option-size__item",
        "quantity": "#quantity-input, input[name='quantity'], input[aria-label='Số lượng'], .quantity input",
        "plus": "[data-testid='quantity-increase'], .quantity button[aria-label='+'], div:has(> #quantity-input) > button[aria-label='Tăng số lượng']",
        "minus": "[data-testid='quantity-decrease'], .quantity button[aria-label='-'], div:has(> #quantity-input) > button[aria-label='Giảm số lượng']",
        "add": "[data-testid='add-to-cart'], button[name='add'], .product-single__addtocart",
        "cart_count": "[data-testid='cart-count'], .header__cart-count, .cart-count",
        "errors": "[role='alert'], .invalid-feedback, .product-single .error, [data-testid='product-error']",
        "recommendations": "section[aria-label='Gợi ý sản phẩm'] a[ga-tracking-value='product-detail__product-suggestion'], [data-testid='related-products'] a[href], .products-related a[href], .product-recommendations a[href]",
        "cookie": "button.cky-btn-accept, #onetrust-accept-btn-handler",
        "close": "[role='dialog'] button[aria-label='Close'], [role='dialog'] button[aria-label='Đóng']",
    }

    def __init__(self, driver):
        super().__init__(driver)
        self.wait = WebDriverWait(driver, float(os.getenv("PDP_TIMEOUT", "30")),
                                  ignored_exceptions=(StaleElementReferenceException,))
        self.locators = dict(self.LOCATORS)
        path = os.getenv("PDP_LOCATORS_FILE")
        if path:
            overrides = json.loads(Path(path).read_text(encoding="utf-8"))
            unknown = set(overrides) - self.locators.keys()
            if unknown or not all(isinstance(v, str) and v for v in overrides.values()):
                raise ValueError("Invalid PDP locator overrides")
            self.locators.update(overrides)

    # Text-based fallbacks are anchored to the purchase panel, never recommendation cards.
    PURCHASE = "//h1/ancestor::*[.//*[@id='product-detail-add-cart']][1]"
    FALLBACKS = {
        "sku": PURCHASE + "//*[contains(normalize-space(.), 'Mã sản phẩm:') and not(.//*[contains(normalize-space(.), 'Mã sản phẩm:')])] | " + PURCHASE + "//*[contains(normalize-space(.), 'Mã sản phẩm:') and not(.//*[contains(normalize-space(.), 'Mã sản phẩm:')])]/parent::*",
        "price": PURCHASE + "//*[contains(., 'đ') or contains(., '₫') or contains(., 'VND')]",
        "sizes": "//*[@id='product-detail-variants']//ul/li/button",
        "add": "//*[@id='product-detail-add-cart']",
        "information": "//*[@id='product-description'][.//*[contains(., 'CHẤT LIỆU')] and .//*[contains(., 'KIỂU DÁNG')]] | //*[@id='product-description']//*[self::section or self::dl or self::div][.//*[contains(., 'CHẤT LIỆU')] and .//*[contains(., 'KIỂU DÁNG')]]",
        "images": "//*[@id='product-gallery']//img",
    }
    VND = re.compile(r"(?:[1-9]\d{0,2}(?:[.,]\d{3})+|[1-9]\d*)\s*(?:đ|₫|VND)", re.I)

    def raw_elements(self, key):
        matches = self.driver.find_elements(By.CSS_SELECTOR, self.locators[key])
        if key in self.FALLBACKS:
            matches += self.driver.find_elements(By.XPATH, self.FALLBACKS[key])
        return list({e.id: e for e in matches}.values())

    def elements(self, key):
        result = []
        for e in self.raw_elements(key):
            try:
                if not e.is_displayed():
                    continue
                value = e.text.strip()
                if key == "sku" and not re.fullmatch(r"Mã sản phẩm:\s*\S+", value):
                    continue
                if key == "price":
                    if not self.VND.fullmatch(value):
                        continue
                    context = e.find_element(By.XPATH, "..").text.casefold()
                    if any(w in context for w in ("coolcash", "voucher", "với mã")):
                        continue
                    if e.find_elements(By.XPATH, "ancestor::del | ancestor::s"):
                        continue
                if key == "sizes" and not re.fullmatch(r"(?:[2-9]?X{0,3}[SML]|[2-9]XL|\d{2})", value):
                    continue
                if key == "images" and not self.product_image(e):
                    continue
                result.append(e)
            except StaleElementReferenceException:
                continue
        return result

    def product_image(self, image):
        return self.driver.execute_script("""
            const e=arguments[0], gallery=document.querySelector('#product-gallery');
            // The promotional overlay is a sibling of this container and shares product alt text.
            return e.tagName === 'IMG' && !!gallery && gallery.contains(e) &&
                !e.closest('header,footer,nav,#product-description,[data-product-id],a[href*="/product/"]');
        """, image)

    def scroll_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

    def field_text(self, key):
        for e in self.elements(key):
            value = e.text.strip()
            if key == "sku":
                value = re.sub(r"^Mã sản phẩm:\s*", "", value)
            # A title-only description is not product content.
            if key in ("description", "information"):
                content = re.sub(r"mô tả sản phẩm|thông tin sản phẩm|đặc điểm sản phẩm",
                                 "", value, flags=re.I).strip()
                if not content:
                    continue
            if value:
                return value
        return ""


    def element(self, key):
        try:
            return self.wait.until(lambda _: next(iter(self.elements(key)), False), message=key)
        except TimeoutException:
            self.timeout_diagnostics(key)
            raise

    def timeout_diagnostics(self, reason):
        """Read-only evidence, including hidden matches; never replace the original failure."""
        folder = Path(__file__).resolve().parents[1] / "results" / "pdp_evidence"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            stem = folder / datetime.now().strftime("timeout_%Y%m%d_%H%M%S_%f")
            data = {"reason": reason, "url": self.driver.current_url,
                    "title": self.driver.title, "locators": self.locators}
            data["dom"] = self.driver.execute_script("""
                const inspect = e => {
                    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
                    const visible = r.width > 0 && r.height > 0 &&
                        s.display !== 'none' && s.visibility !== 'hidden';
                    const top = visible ? document.elementFromPoint(
                        r.x + r.width/2, r.y + r.height/2) : null;
                    return {tag:e.tagName, id:e.id, class:e.className,
                        text:(e.innerText || e.textContent || '').trim().slice(0,300),
                        visible, disabled:!!e.disabled,
                        ariaDisabled:e.getAttribute('aria-disabled'),
                        coveredBy:top && !e.contains(top) ?
                            {tag:top.tagName,id:top.id,class:top.className} : null};
                };
                return {readyState:document.readyState,
                    // Diagnostic only: hidden identifiers never satisfy UI assertions.
                    visibleText:document.body.innerText,
                    identifiers:Array.from(document.querySelectorAll(
                        '[itemprop="sku"],[itemprop="productID"],[data-testid="product-sku"],'
                        + '[id*="sku" i],[class*="sku" i],[id*="product-code" i],'
                        + '[class*="product-code" i]'
                    )).map(e => ({...inspect(e), html:e.outerHTML.slice(0,2000)})),
                    buttons:Array.from(document.querySelectorAll(
                        'button,[role="button"],input[type="submit"],a')).filter(e =>
                        /thêm.*giỏ|mua ngay|add.*cart|buy now/i.test(
                            e.innerText || e.value || e.getAttribute('aria-label') || '')
                    ).map(inspect),
                    overlays:Array.from(document.querySelectorAll(
                        '[role="dialog"],[aria-modal="true"],#onetrust-banner-sdk,.cky-consent-container'
                    )).map(inspect)};
            """)
            data["fallback_locators"] = self.FALLBACKS
            data["checks"] = getattr(self, "pdp_checks", {})
            data["selected_sizes"] = self.selected_labels("sizes")
            data["stock_attempt"] = getattr(self, "stock_attempt", {})
            data["gallery_candidates"] = self.driver.execute_script("""
                return Array.from(document.images).filter(e => !e.closest('header,footer,nav')).map(e => ({
                    html:e.outerHTML, parent:e.parentElement.outerHTML.slice(0,1500),
                    complete:e.complete, naturalWidth:e.naturalWidth, currentSrc:e.currentSrc,
                    srcset:e.srcset, visible:!!(e.getClientRects().length)
                }));
            """)
            accepted = {key: {e.id for e in self.elements(key)} for key in self.locators}
            data["matches"] = {key: [{"displayed": e.is_displayed(),
                                      "enabled": e.is_enabled(), "tag": e.tag_name,
                                      "text": e.text, "html": e.get_attribute("outerHTML")[:3000],
                                      "naturalWidth": e.get_property("naturalWidth") if e.tag_name == "img" else None,
                                      "complete": e.get_property("complete") if e.tag_name == "img" else None,
                                      "currentSrc": e.get_property("currentSrc") if e.tag_name == "img" else None,
                                      "srcset": e.get_attribute("srcset") if e.tag_name == "img" else None,
                                      "selected": self.selected(e) if key == "sizes" and e.is_displayed() else None,
                                      "disabled": self.disabled(e),
                                      "accepted": e.id in accepted[key]}
                                     for e in self.raw_elements(key)]
                               for key, css in self.locators.items()}
            data["items"] = {
                key: {"locator": self.locators[key], "fallback_xpath": self.FALLBACKS.get(key),
                      "found": len(rows), "displayed": sum(r["displayed"] for r in rows),
                      "accepted": sum(r["accepted"] for r in rows),
                      "texts": [r["text"] for r in rows],
                      "result": data["checks"].get(key, {}),
                      "reason": ("No DOM matches" if not rows else
                                 "All matches hidden" if not any(r["displayed"] for r in rows) else
                                 "Visible matches rejected by field validation" if not any(r["accepted"] for r in rows) else
                                 data["checks"].get(key, {}).get("reason", "Qualified visible matches found"))}
                for key, rows in data["matches"].items()}
            data["items"]["in_stock"] = {
                "locator": {key: data["items"][key] for key in ("sizes", "colors", "add")},
                "result": data["checks"].get("in_stock", {}),
                "reason": data["checks"].get("in_stock", {}).get("reason", "See variant/Add evidence")}
            data["purchase_panel_html"] = [e.get_attribute("outerHTML")[:100000]
                                          for e in self.driver.find_elements(By.XPATH, self.PURCHASE)]
            try:
                data["screenshot_saved"] = self.driver.save_screenshot(str(stem) + ".png")
            except Exception as exc:
                data["screenshot_error"] = type(exc).__name__
            Path(str(stem) + ".json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"PDP timeout: {data['url']} | {data['title']} | evidence: {stem}")
        except Exception as exc:
            print(f"PDP diagnostics unavailable: {type(exc).__name__}")

    def dismiss_pdp_overlays(self):
        super().dismiss_popups()
        for key in ("cookie", "close"):
            for element in self.elements(key):
                if element.is_enabled():
                    element.click()
                    self.wait.until(EC.invisibility_of_element(element))

    def dismiss_pdp02_popups(self, initial=False):
        """PDP-02 only: identify consent by its button, never by backdrop colour."""
        from pages.register_page import RegisterPage

        overlay = (By.CSS_SELECTOR, 'div.fixed.inset-0[class~="z-[9990]"]')
        cookie = RegisterPage.COOKIE_ACCEPT_BTN

        def visible(locator):
            return [e for e in self.driver.find_elements(*locator) if e.is_displayed()]

        if initial:
            try:
                WebDriverWait(self.driver, 5, poll_frequency=0.25,
                              ignored_exceptions=(StaleElementReferenceException,)).until(
                    lambda _: visible(cookie) or visible(overlay))
            except TimeoutException:
                return

        def cleared(_):
            backdrops, buttons = visible(overlay), visible(cookie)
            if buttons:
                # Preserve the actual popup DOM for identification on the live run.
                folder = Path(__file__).resolve().parents[1] / "results" / "pdp_evidence"
                folder.mkdir(parents=True, exist_ok=True)
                containers = buttons[0].find_elements(By.XPATH,
                    "ancestor::*[.//div[contains(concat(' ',normalize-space(@class),' '),"
                    " ' z-[9990] ')]][1]")
                (folder / "pdp02_cookie_popup.html").write_text(
                    (containers[0] if containers else buttons[0]).get_attribute("outerHTML"),
                    encoding="utf-8")
                RegisterPage(self.driver).accept_cookies()
                return False
            if backdrops:
                # Only use explicit close controls in the popup owning the backdrop.
                for backdrop in backdrops:
                    owners = backdrop.find_elements(By.XPATH,
                        "ancestor::*[@role='dialog' or @aria-modal='true']"
                        "[.//button[@aria-label='Close' or @aria-label='Đóng']][1]")
                    if owners:
                        for button in owners[0].find_elements(By.CSS_SELECTOR,
                                "button[aria-label='Close'], button[aria-label='Đóng']"):
                            if button.is_displayed() and button.is_enabled():
                                button.click()
                                return False
                return False
            return True

        try:
            self.wait.until(cleared, message="PDP-02 popup and z-[9990] overlay disappeared")
        except TimeoutException:
            self.timeout_diagnostics("PDP-02 unidentified or persistent popup overlay")
            folder = Path(__file__).resolve().parents[1] / "results" / "pdp_evidence"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "pdp02_blocking_popup.html").write_text(
                "\n".join(e.find_element(By.XPATH, "..").get_attribute("outerHTML")
                          for e in visible(overlay)), encoding="utf-8")
            raise

    def open_url(self, url):
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in ("coolmate.me", "www.coolmate.me"):
            raise ValueError("PDP URL must be an HTTPS Coolmate URL")
        if not parts.path.startswith("/product/") or not parts.path[len("/product/"):].strip("/"):
            raise PDPDataUnavailable("Configured PDP URL is not a /product/<slug> URL")
        try:
            self.driver.get(url)
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete",
                            message="document load")
            actual = urlsplit(self.driver.current_url)
            if (actual.hostname not in ("coolmate.me", "www.coolmate.me")
                    or actual.path.rstrip("/") != parts.path.rstrip("/")):
                raise PDPDataUnavailable(f"PDP redirected: {url} -> {self.driver.current_url}")
            self.dismiss_pdp_overlays()
            # Exact product path plus a rendered product heading establish navigation.
            # Completeness (including the visible product code) belongs to assertions.
            self.text("name")
        except TimeoutException as exc:
            self.timeout_diagnostics("open_url: document load or visible product name")
            raise AssertionError(
                "PDP chưa sẵn sàng: document chưa tải xong hoặc thiếu tên sản phẩm hiển thị; "
                f"URL={self.driver.current_url} | title={self.driver.title}"
            ) from exc
        return self

    @staticmethod
    def label(element):
        swatches = element.find_elements(By.CSS_SELECTOR, "img[alt^='color ']")
        if swatches:
            return swatches[0].get_attribute("alt")[len("color "):].strip()
        return (element.get_attribute("data-value") or element.get_attribute("aria-label")
                or element.get_attribute("title") or element.text).strip()

    @staticmethod
    def selected(element):
        # Color links in the saved DOM navigate with ?color=; borders also
        # appear on hover, so they cannot establish selection.
        if element.tag_name == "a" and element.find_elements(By.CSS_SELECTOR, "img[alt^='color ']"):
            from urllib.parse import parse_qs
            target = urlsplit(element.get_attribute("href"))
            current = urlsplit(element.parent.execute_script("return location.href"))
            return (target.path == current.path and bool(parse_qs(target.query).get("color"))
                    and parse_qs(target.query).get("color") == parse_qs(current.query).get("color"))
        classes = set((element.get_attribute("class") or "").split())
        return (element.is_selected() or element.get_attribute("aria-checked") == "true"
                or element.get_attribute("aria-selected") == "true"
                or element.get_attribute("aria-pressed") == "true"
                or element.get_attribute("data-state") in ("checked", "selected")
                or bool(classes & {"selected", "active", "is-selected", "is-active"})
                # Observed Coolmate size buttons use exact Tailwind tokens, not hover tokens.
                or (element.tag_name == "button"
                    and re.fullmatch(r"(?:[2-9]?X{0,3}[SML]|[2-9]XL|\d{2})", element.text.strip())
                    and bool(element.find_elements(By.XPATH, "ancestor::*[@id='product-detail-variants']"))
                    and {"bg-neutral-900", "text-light"}.issubset(classes)))

    # Verified in results/pdp_evidence/pdp02_cookie_popup.html: sold-out size
    # buttons are CSS-blocked and crossed out with two pseudo-elements, without
    # native disabled/ARIA attributes. Scope this signature to the size panel.
    SOLDOUT_SIZE_CLASSES = frozenset({
        "pointer-events-none", "cursor-not-allowed", "before:rotate-[30deg]",
        "after:rotate-[145deg]", "before:border-dashed", "after:border-dashed",
    })

    @staticmethod
    def disabled(element):
        classes = set((element.get_attribute("class") or "").split())
        return (not element.is_enabled() or element.get_attribute("aria-disabled") == "true"
                or element.get_attribute("data-disabled") in ("true", "")
                or bool(classes & {"disabled", "soldout", "sold-out", "is-disabled", "out-of-stock", "unavailable"})
                or (element.tag_name == "button"
                    and ProductDetailsMixin.SOLDOUT_SIZE_CLASSES.issubset(classes)
                    and bool(element.find_elements(By.XPATH,
                        "parent::li/parent::ul/ancestor::*[@id='product-detail-variants']"))))

    def options(self, key):
        return [{"label": self.label(e), "selected": self.selected(e), "disabled": self.disabled(e)}
                for e in self.elements(key)]

    def option(self, key, label):
        return self.wait.until(lambda _: next((e for e in self.elements(key)
                                               if self.label(e) == label), False))

    def choose(self, key, label):
        # Consent may arrive after open_url(), including while scrolling the PDP.
        self.dismiss_pdp02_popups()
        element = self.option(key, label)
        if self.disabled(element):
            raise ValueError("Cannot choose disabled variant")
        if self.selected_labels(key) == [label]:
            return
        self.scroll_element(element)
        before = self.variant_evidence(key)
        try:
            try:
                element.click()
            except ElementClickInterceptedException:
                self.dismiss_pdp02_popups(initial=True)
                # Reacquire after the popup/possible route render; never click through it.
                element = self.option(key, label)
                if self.disabled(element):
                    raise ValueError("Cannot choose disabled variant")
                if self.selected_labels(key) != [label]:
                    element.click()
            self.wait.until(lambda _: self.selected_labels(key) == [label],
                            message=f"exclusive selected {key}: {label}")
        finally:
            self.save_variant_evidence(key, label, before)

    def save_variant_evidence(self, key, label, before):
        try:
            folder = Path(__file__).resolve().parents[1] / "results" / "pdp_evidence"
            folder.mkdir(parents=True, exist_ok=True)
            payload = {"key": key, "requested": label, "before": before,
                       "after": self.variant_evidence(key)}
            (folder / datetime.now().strftime("variant_%Y%m%d_%H%M%S_%f.json")).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            # Diagnostics must never hide the original selection timeout.
            print(f"PDP variant evidence unavailable: {type(exc).__name__}")

    def variant_evidence(self, key):
        """Read-only state for diagnosing duplicate selections and locator scope."""
        if key == "sizes":
            return self.size_state()
        return {"url": self.driver.current_url, "options": [
            {"label": self.label(e), "selected": self.selected(e),
             "native_selected": e.is_selected(), "disabled": self.disabled(e),
             "attributes": {a: e.get_attribute(a) for a in
                            ("class", "aria-pressed", "aria-selected", "aria-checked", "data-state")},
             "html": e.get_attribute("outerHTML"),
             "parent_html": e.find_element(By.XPATH, "..").get_attribute("outerHTML")}
            for e in self.elements(key)]}

    def selected_labels(self, key):
        if key == "sizes":
            return [row["label"] for row in self.size_state()["options"] if row["selected"]]
        return [row["label"] for row in self.options(key) if row["selected"]]

    def size_state(self):
        """Read size DOM/CSS in one browser task, avoiding mixed render generations.

        Exact class tokens come from saved Coolmate DOM. Hover/background colour
        alone is never selection or stock evidence. JS is strictly read-only.
        """
        return self.driver.execute_script("""
            const panel = document.querySelector('#product-detail-variants');
            const options = arguments[0].filter(e => e.isConnected).map(e => {
                const s = getComputedStyle(e), c = new Set(e.classList);
                const attr = n => e.getAttribute(n);
                const explicit = ['aria-checked','aria-selected','aria-pressed'];
                const selected = e.matches(':checked') ||
                    explicit.some(n => attr(n) === 'true') ||
                    ['checked','selected'].includes(attr('data-state')) ||
                    ['selected','active','is-selected','is-active'].some(n => c.has(n)) ||
                    (e.tagName === 'BUTTON' && e.closest('#product-detail-variants') &&
                     c.has('bg-neutral-900') && c.has('text-light'));
                const disabled = e.matches(':disabled') || attr('aria-disabled') === 'true' ||
                    ['true',''].includes(attr('data-disabled')) ||
                    ['disabled','soldout','sold-out','is-disabled','out-of-stock','unavailable']
                        .some(n => c.has(n)) ||
                    (e.tagName === 'BUTTON' && e.matches('ul > li > button') &&
                     e.closest('#product-detail-variants') && arguments[1].every(n => c.has(n)));
                const pseudo = name => {
                    const p = getComputedStyle(e, name);
                    return {content:p.content, transform:p.transform, rotate:p.rotate,
                        borderTopStyle:p.borderTopStyle, borderTopWidth:p.borderTopWidth,
                        color:p.color, pointerEvents:p.pointerEvents};
                };
                return {label:(attr('data-value') || attr('aria-label') || attr('title') || e.innerText).trim(),
                    selected:!!selected, native_selected:e.matches(':checked'), disabled,
                    html:e.outerHTML, parent_html:e.parentElement.outerHTML,
                    attributes:Object.fromEntries(Array.from(e.attributes, a => [a.name,a.value])),
                    css:{background:s.backgroundColor, color:s.color, opacity:s.opacity,
                        pointerEvents:s.pointerEvents, cursor:s.cursor, textDecoration:s.textDecorationLine},
                    pseudo:{before:pseudo('::before'), after:pseudo('::after')},
                    hovered:e.matches(':hover')};
            });
            const text = panel ? panel.innerText : '';
            const match = text.match(/Kích thước\\s*:\\s*([^\\n\\r]+)/i);
            return {url:location.href, options, size_label:match ? match[1].trim() : '',
                panel_text:text, panel_html:panel ? panel.outerHTML : ''};
        """, self.elements("sizes"), sorted(self.SOLDOUT_SIZE_CLASSES))

    def text(self, key):
        try:
            return self.wait.until(lambda _: self.field_text(key),
                message=f"non-empty {key}")
        except TimeoutException:
            self.timeout_diagnostics(key)
            raise

    def image_sources(self, *, pdp02_gallery=None):
        """Loaded browser-selected URLs, preserving every query parameter exactly.

        Default: displayed gallery IMG elements (legacy PDP-01 contract).
        PDP-02 snapshot: all images with positive clipped area, including edge
        slivers; not just the selected slide and not the whole hidden library.
        Never infer identity from filenames, srcset candidates or data-src.
        """
        # PDP-01 retains its existing contract. PDP-02 and its evidence collector
        # use the same atomic snapshot, clipping scope and loaded-image predicate.
        if pdp02_gallery is not None:
            return [r["currentSrc"] or r["src"]
                    for g in pdp02_gallery for r in g["images"]
                    if r["visibleInGallery"] and r["complete"] and r["naturalWidth"] > 0]
        images = self.elements("images")
        return [e.get_property("currentSrc") or e.get_attribute("src") for e in images
                if e.get_property("complete") and (e.get_property("naturalWidth") or 0) > 0]

    def price(self):
        return self.text("price")

    def pdp02_verify_oracle_images(self, sources):
        """Verify actual primary images by native thumbnail clicks, not hidden IMG presence."""
        observed = []
        first_button = None
        self.pdp02_verified_gallery = []

        def primary():
            rows = [r for g in self.pdp02_gallery_state() for r in g["images"]
                    if r["visibleInGallery"] and r["onScreen"]]
            return max(rows, key=lambda r: r["clippedArea"]) if rows else None

        def loaded_primary(source):
            row = primary()
            return (row and row["complete"] and row["naturalWidth"] > 0
                    and (row["currentSrc"] or row["src"]) == source)

        gallery = self.element("images")
        self.scroll_element(gallery)
        # Do not mask a stale/wrong image on the initial colour transition.
        self.wait.until(lambda _: loaded_primary(sources[0]),
                        message="PDP-02 initial primary image must match selected colour oracle")
        for source in sources:
            path = urlsplit(source).path
            gallery = self.driver.find_element(By.ID, "product-gallery")
            owner = gallery.find_element(By.XPATH, "../..")
            buttons = owner.find_elements(By.CSS_SELECTOR, "button:has(img)")
            button = next((b for b in buttons if b.get_attribute("aria-label") != "Play video"
                           and any(urlsplit(img.get_attribute("src") or "").path == path
                                   for img in b.find_elements(By.CSS_SELECTOR, "img"))), None)
            if button is None:
                raise TimeoutException(f"PDP-02 no native thumbnail for oracle image {source}")
            if first_button is None:
                first_button = button
            self.dismiss_pdp02_popups()
            self.scroll_element(button)
            self.wait.until(EC.element_to_be_clickable(button)).click()
            self.scroll_element(self.driver.find_element(By.ID, "product-gallery").find_element(By.XPATH, ".."))
            self.wait.until(lambda _: loaded_primary(source),
                            message=f"PDP-02 clicked thumbnail did not display {source}")
            row = primary()
            observed.append(row["currentSrc"] or row["src"])
            folder = Path("results/pdp0205_fix")
            folder.mkdir(parents=True, exist_ok=True)
            screenshot = folder / datetime.now().strftime("gallery_%Y%m%d_%H%M%S_%f.png")
            self.driver.save_screenshot(str(screenshot))
            self.pdp02_verified_gallery.append({
                "url": self.driver.current_url, "expected": source, "actual": observed[-1],
                "primary": row, "gallery": self.pdp02_gallery_state(),
                "thumbnail_html": button.get_attribute("outerHTML"), "screenshot": str(screenshot)})
        # Keep the same starting slide for the next colour transition.
        if len(sources) > 1:
            self.dismiss_pdp02_popups()
            self.scroll_element(first_button)
            self.wait.until(EC.element_to_be_clickable(first_button)).click()
            self.scroll_element(self.driver.find_element(By.ID, "product-gallery").find_element(By.XPATH, ".."))
            self.wait.until(lambda _: loaded_primary(sources[0]),
                            message="PDP-02 restore first verified image before changing colour")
        return observed

    def pdp02_image_debug(self):
        """Read-only image provenance; never changes the image assertion/filter."""
        return self.driver.execute_script(r"""
            const accepted = new Set(arguments[0]);
            return Array.from(document.images).filter(e =>
                /uploads\//i.test(e.currentSrc || e.src || e.getAttribute('data-src') || '')).map(e => {
                const gallery = e.closest('#product-gallery');
                const ancestors = []; let p = e.parentElement;
                for (let i=0; p && i<4; i++,p=p.parentElement)
                    ancestors.push({tag:p.tagName,id:p.id,class:p.className,role:p.getAttribute('role')});
                return {src:e.src,currentSrc:e.currentSrc,srcset:e.srcset,
                    dataSrc:e.getAttribute('data-src'),alt:e.alt,loading:e.loading,
                    loaded:e.complete && e.naturalWidth>0,naturalWidth:e.naturalWidth,
                    lazy_pending:e.loading==='lazy' && !(e.complete && e.naturalWidth>0),
                    rendered:!!e.getClientRects().length,in_gallery:!!gallery,
                    container:gallery ? {tag:gallery.tagName,id:gallery.id,class:gallery.className} : null,
                    accepted_by_image_sources:accepted.has(e),
                    advertising_hint:/FT[_-]*80k|voucher|banner/i.test(e.src+' '+e.alt),
                    recommendation:!!e.closest('[data-product-id],a[href*="/product/"]'),ancestors};
            });
        """, self.elements("images"))

    def pdp02_gallery_state(self):
        """Atomic, read-only geometry: distinguish clipped slides from stale visible UI.

        Keep every gallery, including duplicate IDs left during route transitions.
        No colour/filename filtering: an old visible image must remain a failure.
        """
        return self.driver.execute_script(r"""
            const rect = e => {
                const r=e.getBoundingClientRect();
                return {x:r.x,y:r.y,width:r.width,height:r.height};
            };
            const galleries=Array.from(document.querySelectorAll('[id="product-gallery"]'));
            return galleries.map((g,gi) => {
                const viewport=g.parentElement, vr=viewport.getBoundingClientRect();
                const rows=Array.from(g.querySelectorAll('img')).map((e,index) => {
                    const r=e.getBoundingClientRect(), s=getComputedStyle(e);
                    let left=r.left,right=r.right,top=r.top,bottom=r.bottom, hidden=false;
                    for(let p=e;p;p=p.parentElement) {
                        const ps=getComputedStyle(p), pr=p.getBoundingClientRect();
                        hidden ||= ps.display==='none' || ps.visibility==='hidden' || Number(ps.opacity)===0;
                        if(p!==e) {
                            if(/hidden|clip|scroll|auto/.test(ps.overflowX)) {
                                left=Math.max(left,pr.left); right=Math.min(right,pr.right);
                            }
                            if(/hidden|clip|scroll|auto/.test(ps.overflowY)) {
                                top=Math.max(top,pr.top); bottom=Math.min(bottom,pr.bottom);
                            }
                        }
                    }
                    const area=Math.max(0,right-left)*Math.max(0,bottom-top);
                    const onScreen=area>1 && right>0 && bottom>0 && left<innerWidth && top<innerHeight;
                    const hit=onScreen ? document.elementFromPoint(
                        Math.max(0,Math.min(innerWidth-1,(left+right)/2)),
                        Math.max(0,Math.min(innerHeight-1,(top+bottom)/2))) : null;
                    const slide=e.closest('#product-gallery > *');
                    return {index,src:e.src,currentSrc:e.currentSrc,srcset:e.srcset,
                        alt:e.alt,loading:e.loading,complete:e.complete,naturalWidth:e.naturalWidth,
                        css:{display:s.display,visibility:s.visibility,opacity:s.opacity},
                        clippedRect:{left,right,top,bottom},
                        rect:rect(e),clippedArea:area,
                        visibleFraction:r.width*r.height>0 ? area/(r.width*r.height) : 0,
                        visibleInGallery:!hidden && area>1,
                        onScreen,hitAtCenter:hit===e || !!(hit && slide && slide.contains(hit)),
                        coveredBy:hit ? {tag:hit.tagName,id:hit.id,class:hit.className} : null,
                        slide:slide ? {class:slide.className,rect:rect(slide),
                            ariaHidden:slide.getAttribute('aria-hidden'),
                            ariaCurrent:slide.getAttribute('aria-current'),
                            dataState:slide.getAttribute('data-state'),
                            transform:getComputedStyle(slide).transform} : null};
                });
                return {index:gi,class:g.className,rect:rect(g),viewport:rect(viewport),
                    overflow:getComputedStyle(viewport).overflow,
                    transform:getComputedStyle(g).transform,scrollLeft:viewport.scrollLeft,
                    animations:g.getAnimations({subtree:true}).filter(a=>a.playState==='running')
                        .map(a=>({playState:a.playState,currentTime:a.currentTime})),
                    activeSlides:rows.filter(r=>r.visibleInGallery).map(r=>r.index),images:rows,
                    controls:Array.from(viewport.parentElement.querySelectorAll('button')).map(b=>({
                        text:b.innerText,label:b.getAttribute('aria-label'),title:b.title,
                        disabled:b.disabled,html:b.outerHTML.slice(0,1200)}))};
            });
        """)

    @staticmethod
    def price_vnd(value):
        """Parse one whole VND amount; reject labels/multiple prices rather than concatenate."""
        compact = re.sub(r"\s+", "", str(value))
        if not re.fullmatch(r"(?:\d{1,3}(?:[.,]\d{3})+|\d+)(?:đ|₫|VND)?", compact, re.I):
            raise ValueError(f"Not a single VND amount: {value!r}")
        return int(re.sub(r"\D", "", compact))

    def variant_price_debug(self):
        """PDP-02 only: inspect the exact first source used by price(), without waiting."""
        accepted = self.elements("price")
        panels = self.driver.find_elements(By.XPATH, self.PURCHASE)
        rows = []
        for e in self.raw_elements("price"):
            context = e.find_element(By.XPATH, "..").text
            in_panel = bool(panels and self.driver.execute_script(
                "return arguments[0].contains(arguments[1]);", panels[0], e))
            recommendation = bool(e.find_elements(By.XPATH,
                "ancestor::a[contains(@href, '/product/')] | ancestor::*[@data-product-id or "
                "@data-testid='related-products' or contains(@class,'products-related') or "
                "contains(@class,'product-recommendations')]"))
            safe = (in_panel and not recommendation
                    and not any(w in context.casefold() for w in ("voucher", "coolcash", "với mã")))
            rows.append({"used_by_price": bool(accepted and e.id == accepted[0].id),
                         "accepted": any(e.id == a.id for a in accepted), "safe_source": safe,
                         "text": e.text, "textContent": e.get_attribute("textContent"),
                         "visible": e.is_displayed(), "context": context[:600],
                         "html": e.get_attribute("outerHTML")[:2000]})
        return {"css": self.locators["price"], "xpath": self.FALLBACKS["price"],
                "actual": self.field_text("price"), "candidates": rows}

    def snapshot(self, visible_only=False):
        if visible_only:
            # PDP-01 reads rendered UI, revealing lower sections through UI controls.
            # Each field has a bounded wait; failures are aggregated rather than hidden.
            previous_wait = self.wait
            self.wait = WebDriverWait(self.driver, min(float(os.getenv("PDP_TIMEOUT", "30")), 8),
                                      poll_frequency=0.25,
                                      ignored_exceptions=(StaleElementReferenceException,))
            state = {}
            self.pdp_checks = {}
            try:
                for key in ("name", "sku", "price", "images", "sizes", "description", "information"):
                    try:
                        if key in ("images", "sizes", "description", "information"):
                            self.reveal_details(key)
                        def collect(_):
                            if key == "images":
                                return self.image_sources()
                            if key == "sizes":
                                return self.options(key)
                            return self.field_text(key)
                        state[key] = self.wait.until(collect, message=key)
                        self.pdp_checks[key] = {"passed": True, "value": state[key]}
                    except WebDriverException as exc:
                        state[key] = [] if key in ("images", "sizes") else ""
                        self.pdp_checks[key] = {"passed": False, "reason": f"{type(exc).__name__}: {exc}"}
                try:
                    state["in_stock"] = self.verify_in_stock()
                    self.pdp_checks["in_stock"] = {"passed": True, "value": state["in_stock"]}
                except (WebDriverException, ValueError) as exc:
                    state["in_stock"] = False
                    self.pdp_checks["in_stock"] = {"passed": False, "reason": str(exc)}
            finally:
                self.wait = previous_wait
            if not all(state.values()):
                self.timeout_diagnostics("PDP-01 incomplete UI evidence")
            return state
        try:
            self.wait.until(lambda _: self.image_sources(), message="loaded product image")
        except TimeoutException:
            self.timeout_diagnostics("loaded product image")
            raise
        return {"name": self.text("name"), "sku": self.text("sku"), "price": self.price(),
                "images": self.image_sources(), "description": self.text("description"),
                "information": self.text("information"), "sizes": self.wait_for_sizes()}

    def reveal_details(self, key):
        if key == "images":
            # Do not require is_displayed() before scrolling it back into view.
            # Scroll the viewport, not a hidden/offscreen carousel slide (which can
            # move the carousel horizontally). Loading is checked by the caller.
            def reveal(_):
                galleries = self.driver.find_elements(By.CSS_SELECTOR, '[id="product-gallery"]')
                for gallery in galleries:
                    viewport = gallery.find_element(By.XPATH, "..")
                    if viewport.rect["width"] > 0 and viewport.rect["height"] > 0:
                        self.scroll_element(viewport)
                        return viewport
                return False
            viewport = self.wait.until(reveal, message="product gallery viewport")
            # Saved DOM starts on a video slide. Loaded carousel images remain
            # clipped, so scrolling alone cannot reveal a photo. Use its actual
            # thumbnail; never count the video poster/hidden library as an image.
            videos = viewport.find_elements(By.CSS_SELECTOR, "video")
            if not self.elements("images") and any(v.is_displayed() for v in videos):
                self.dismiss_pdp02_popups()
                panel = viewport.find_element(By.XPATH, "..")
                thumbnails = panel.find_elements(By.CSS_SELECTOR,
                    'button:has(img):not(:has(img[alt*="video"]))')
                photos = [b for b in thumbnails if b.is_displayed() and b.is_enabled()]
                if photos:
                    self.scroll_element(photos[0])
                    try:
                        photos[0].click()
                    except ElementClickInterceptedException:
                        self.dismiss_pdp02_popups(initial=True)
                        buttons = panel.find_elements(By.CSS_SELECTOR,
                            'button:has(img):not(:has(img[alt*="video"]))')
                        next(b for b in buttons if b.is_displayed() and b.is_enabled()).click()
            return
        if key == "sizes":
            self.scroll_element(self.element("add"))
            return
        # Open only description/information controls via real Selenium clicks.
        controls = self.driver.find_elements(By.CSS_SELECTOR,
            "button[aria-controls], [role='tab'], summary, a[href='#product-description']")
        for control in controls:
            try:
                label = control.text.strip().casefold()
                if control.is_displayed() and any(t in label for t in
                        ("mô tả sản phẩm", "thông tin sản phẩm", "đặc điểm sản phẩm")):
                    self.scroll_element(control)
                    if control.get_attribute("aria-expanded") == "false" or (
                            control.get_attribute("role") == "tab" and
                            control.get_attribute("aria-selected") != "true") or (
                            control.tag_name == "summary" and not
                            control.find_element(By.XPATH, "..").get_attribute("open")):
                        control.click()
            except StaleElementReferenceException:
                continue
        candidates = self.raw_elements(key) or self.raw_elements("description")
        if candidates:
            self.scroll_element(candidates[0])

    def verify_in_stock(self):
        self.scroll_element(self.element("add"))
        sizes = self.wait_for_sizes()
        available = [s for s in sizes if not s["disabled"]]
        if not available:
            raise ValueError(f"No enabled size for the current color; observed sizes={sizes}")
        selected = [s for s in available if s["selected"]]
        chosen_label = (selected or available)[0]["label"]
        self.stock_attempt = {"available_sizes": available, "chosen_size": chosen_label}
        self.choose("sizes", chosen_label)
        def purchasable(_):
            chosen = [s for s in self.options("sizes") if s["selected"] and not s["disabled"]]
            buttons = self.elements("add")
            return bool(chosen and buttons and not self.disabled(buttons[0]) and
                        re.search(r"thêm.*giỏ|add.*cart", buttons[0].text, re.I) and
                        not re.search(r"hết hàng|sold out|thông báo", buttons[0].text, re.I) and
                        (not self.options("colors") or self.selected_labels("colors")))
        return self.wait.until(purchasable, message="Selected available variant and enabled Add button")

    def wait_for_sizes(self):
        try:
            return self.wait.until(lambda _: self.options("sizes"), message="product sizes")
        except TimeoutException:
            self.timeout_diagnostics("sizes")
            raise

    def cart_count(self):
        # Missing badge is NOT assumed to mean an empty cart.
        element = self.element("cart_count")
        value = element.get_attribute("data-count") or element.text
        if not re.fullmatch(r"\s*\d+\s*", value or ""):
            raise ValueError("Cart count has no reliable numeric evidence")
        return int(value)

    def add_to_cart(self):
        self.dismiss_pdp_overlays()
        element = self.element("add")
        if self.disabled(element):
            return False
        element.click()
        return True

    def errors(self):
        return " ".join(e.text.strip() for e in self.elements("errors") if e.text.strip())

    def quantity_diagnostics(self, reason):
        """PDP-06 evidence, including candidates rejected by the active mapping."""
        folder = Path(__file__).resolve().parents[1] / "results" / "pdp06_debug"
        folder.mkdir(parents=True, exist_ok=True)
        stem = folder / datetime.now().strftime("quantity_%Y%m%d_%H%M%S_%f")
        try:
            data = {"reason": reason, "url": self.driver.current_url,
                    "title": self.driver.title, "locators": self.locators}
            data["dom"] = self.driver.execute_script("""
                const inspect = e => {
                    const r=e.getBoundingClientRect();
                    const top=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                    return {html:e.outerHTML, value:e.value ?? e.innerText,
                        visible:!!e.getClientRects().length,
                        disabled:!!e.disabled, ariaDisabled:e.getAttribute('aria-disabled'),
                        coveredBy:top && !e.contains(top) ? top.outerHTML.slice(0,1500):null,
                        container:e.parentElement.outerHTML.slice(0,12000)};
                };
                return {readyState:document.readyState,
                    candidates:Array.from(document.querySelectorAll('button,input,#quantity-input,[role="button"]'))
                        .filter(e=>/quantity/i.test(
                            (e.getAttribute('aria-label')||'')+' '+
                            (e.getAttribute('ga-tracking-value')||'')+' '+e.id) ||
                            /^[+\u2212-]$/.test(e.textContent.trim())).map(inspect),
                    overlays:Array.from(document.querySelectorAll(
                        '[role="dialog"],[aria-modal="true"],div.fixed.inset-0')).map(inspect),
                    cookieButtons:Array.from(document.querySelectorAll('button'))
                        .filter(e=>/Ch\u1ea5p nh\u1eadn t\u1ea5t c\u1ea3/i.test(e.textContent)).map(inspect)};
            """)
            self.driver.save_screenshot(str(stem)+".png")
            Path(str(stem)+".html").write_text(self.driver.page_source, encoding="utf-8")
            Path(str(stem)+".json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"PDP-06 evidence: {stem}; reason={reason}", flush=True)
        except WebDriverException as exc:
            print(f"PDP-06 evidence unavailable: {type(exc).__name__}: {exc.msg}", flush=True)

    def prepare_quantity_controls(self):
        """PDP-06: one sibling group on PDP, not a cart/recommendation counter."""
        container = ("div:has(> button[ga-tracking-value='product-detail__quantity__increment'])"
                     ":has(> button[ga-tracking-value='product-detail__quantity__decrement'])")
        self.locators.update({
            "quantity": container + " > #quantity-input",
            "plus": container + " > button[ga-tracking-value='product-detail__quantity__increment']",
            "minus": container + " > button[ga-tracking-value='product-detail__quantity__decrement']",
        })
        self._pdp06_quantity = True
        try:
            # Reuses REG consent click and PDP's existing explicit overlay wait.
            self.dismiss_pdp02_popups(initial=True)
            add = self.element("add")
            self.scroll_element(add)
            self.wait.until(lambda _: all(self.elements(k) for k in ("quantity", "plus", "minus")),
                            message="PDP quantity counter and sibling +/- visible in purchase panel")
            self.scroll_element(self.element("quantity"))
            self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.locators["plus"])))
            self.quantity_diagnostics("Controls ready on PDP after consent/scroll")
        except WebDriverException as exc:
            self.quantity_diagnostics(f"Controls not ready: {type(exc).__name__}: {exc.msg}")
            raise

    def set_quantity(self, value):
        element = self.element("quantity")
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(str(value))
        element.send_keys(Keys.TAB)

    def quantity_state(self):
        element = self.element("quantity")
        # Read-only DOM validity API; never alter values or bypass disabled controls.
        validity = self.driver.execute_script(
            "return {valid:arguments[0].validity.valid, message:arguments[0].validationMessage};", element)
        return {"value": element.get_property("value"), "min": element.get_attribute("min"),
                "max": element.get_attribute("max"), "step": element.get_attribute("step"),
                "valid": validity["valid"], "message": validity["message"], "errors": self.errors()}

    def quantity_value(self):
        counter = self.element("quantity")
        value = (counter.get_property("value") if counter.tag_name.lower() == "input"
                 else counter.text)
        assert value is not None and re.fullmatch(r"-?\d+", str(value).strip()), (
            f"Quantity counter is not an integer: {value!r}; "
            f"DOM={counter.get_attribute('outerHTML')}")
        return int(str(value).strip())

    def step_quantity(self, direction):
        assert direction in ("plus", "minus")
        if getattr(self, "_pdp06_quantity", False):
            self.dismiss_pdp02_popups()
            self.scroll_element(self.element(direction))
            self.quantity_diagnostics(f"before click {direction}")
            element = self.element(direction)
            if self.disabled(element):
                return False
            self.wait.until(EC.element_to_be_clickable(element)).click()
            return True
        self.dismiss_pdp_overlays()
        element = self.element(direction)
        if self.disabled(element):
            return False
        element.click()
        return True

    def set_quantity_buttons(self, target):
        assert 1 <= target <= 5, "Only bounded UI quantities 1..5 are supported"
        current = self.quantity_value()
        assert 1 <= current <= 10, "Unexpected initial quantity; no unbounded clicking"
        for _ in range(abs(target - current)):
            before = self.quantity_value()
            direction = "plus" if target > before else "minus"
            assert self.step_quantity(direction), f"{direction} disabled before target {target}"
            expected = before + (1 if direction == "plus" else -1)
            self.wait.until(lambda _: self.quantity_value() == expected)
        assert self.quantity_value() == target

    def try_deselect_variants(self):
        """Probe selected size with a native click; never remove state attributes."""
        self.dismiss_pdp02_popups(initial=True)
        for key in ("sizes", "colors"):
            selected = self.selected_labels(key)
            if selected:
                element = self.option(key, selected[0])
                if not self.disabled(element):
                    self.scroll_element(element)
                    self.dismiss_pdp02_popups()
                    try:
                        self.wait.until(EC.element_to_be_clickable(element)).click()
                    except ElementClickInterceptedException:
                        self.dismiss_pdp02_popups(initial=True)
                        element = self.option(key, selected[0])
                        self.scroll_element(element)
                        self.wait.until(EC.element_to_be_clickable(element)).click()
                    self.dismiss_pdp02_popups()
                    self.element("add")
                    observations = []
                    def settled(_):
                        labels = self.selected_labels(key)
                        observations.append(labels)
                        return len(observations) >= 3 and observations[-3:] == [labels] * 3
                    self.wait.until(settled)
                    # Navigation swatches can restore the default size: probe size first.
                    if not self.selected_labels(key):
                        return

    def recommendation(self):
        # PDP-09 only. Title links are distinct from image/quick-add links.
        section = "section[aria-label='G\u1ee3i \u00fd s\u1ea3n ph\u1ea9m']"
        self.locators["recommendations"] = (
            section + " figure[aria-label='Product card'] figcaption a[href*='/product/']:has(h3)")
        self.dismiss_pdp02_popups(initial=True)
        # Trigger content below the description without jumping past the carousel.
        for key in ("description",):
            for element in self.elements(key)[:1]:
                self.scroll_element(element)
        block = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, section)),
                                message="PDP-09 recommendation section; absence is not a locator SKIP")
        self.scroll_element(block)
        self.dismiss_pdp02_popups()
        self.wait.until(lambda _: self.elements("recommendations"),
                        message="PDP-09 lazy-loaded carousel title links")
        origin = urlsplit(self.driver.current_url)
        for element in self.elements("recommendations"):
            # First displayed title in the carousel is sufficient; do not click quick-add.
            self.scroll_element(element)
            if not self.driver.execute_script("""
                const e=arguments[0],r=e.getBoundingClientRect();
                const t=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);
                return !!t && (e===t || e.contains(t));
            """, element):
                continue
            href = element.get_attribute("href")
            target = urlsplit(href or "")
            name = element.find_element(By.CSS_SELECTOR, "h3").text.strip()
            if (target.hostname == origin.hostname and target.path.startswith("/product/")
                    and target.path != origin.path and name):
                self.pdp09_selected = {"href": href, "name": name,
                                       "html": element.get_attribute("outerHTML")}
                self.recommendation_diagnostics("selected visible carousel product")
                return href, name.strip()
        raise AssertionError("PDP-09 carousel exists but no usable product title/link; inspect evidence")

    def recommendation_diagnostics(self, reason):
        """PDP-09 read-only evidence; never overwrite an earlier run."""
        folder = Path(__file__).resolve().parents[1] / "results" / "pdp09_debug"
        folder.mkdir(parents=True, exist_ok=True)
        stem = folder / datetime.now().strftime("recommendation_%Y%m%d_%H%M%S_%f")
        try:
            data = {"reason": reason, "url": self.driver.current_url,
                    "title": self.driver.title, "selected": getattr(self, "pdp09_selected", None),
                    "locator": self.locators["recommendations"],
                    "windows": self.driver.window_handles}
            data["sections"] = self.driver.execute_script("""
                return Array.from(document.querySelectorAll('section')).map(e=>({
                    aria:e.getAttribute('aria-label'),html:e.outerHTML,
                    visible:!!e.getClientRects().length}));
            """)
            self.driver.save_screenshot(str(stem) + ".png")
            Path(str(stem) + ".html").write_text(self.driver.page_source, encoding="utf-8")
            Path(str(stem) + ".json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"PDP-09 evidence: {stem}", flush=True)
        except (WebDriverException, OSError) as exc:
            print(f"PDP-09 evidence unavailable: {type(exc).__name__}", flush=True)

    def follow_recommendation(self, href):
        element = self.wait.until(lambda _: next((e for e in self.elements("recommendations")
                                                  if e.get_attribute("href") == href), False))
        handles = set(self.driver.window_handles)
        self.scroll_element(element)
        self.dismiss_pdp02_popups()
        self.wait.until(EC.element_to_be_clickable(element)).click()

        def destination_loaded(_):
            new = set(self.driver.window_handles) - handles
            for handle in new:
                self.driver.switch_to.window(handle)
                if urlsplit(self.driver.current_url).path.rstrip("/") == urlsplit(href).path.rstrip("/"):
                    return True
            return urlsplit(self.driver.current_url).path.rstrip("/") == urlsplit(href).path.rstrip("/")

        self.wait.until(destination_loaded, message="PDP-09 selected product URL in current/new tab")
        self.dismiss_pdp02_popups(initial=True)
        self.element("name")
        self.element("add")
