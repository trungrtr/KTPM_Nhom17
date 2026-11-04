# PDP priority fixes ? 2026-11-03

## Causes and changes

Production file changed: `pages/pdp_support.py` only. Existing definitions retained.

PDP-01: latest saved diagnostic `results/pdp_evidence/timeout_20261103_234316_481221.json` has all gallery images displayed=false, including two fully loaded images (naturalWidth=1100). Saved full DOM `pdp02_cookie_popup.html` establishes a leading VIDEO slide, followed by photo slides, with photo thumbnail buttons outside the viewport. Thus loaded library images do not establish a displayed photo; the old reveal helper only scrolled an already displayed image and could not leave the video slide. The helper now scrolls the gallery viewport, and when a video is displayed with no displayed photo, clicks the first photo thumbnail using Selenium. The existing polling check for displayed product images, complete, positive naturalWidth and currentSrc-or-src remains intact. No hidden image, poster, srcset candidate or data-src is substituted. This is a repair based on stored DOM; fresh UI confirmation is pending.

PDP-02: existing helper/test use clipped visible gallery scope, including edge slivers. Stored black timeout has expected primary photo plus an extra neighbouring photo whose clipped width is about 0.3625 CSS px. Gray/beige oracles include equivalent neighbours. The oracle scope is inconsistent; neither primary-active nor whole-carousel scope can be substituted without reviewing expected results. Exact URL/set assertions and oracle are unchanged. Replay confirms existing reader produces the same two-image sets for black/gray/beige. No website wrong-colour defect is established by this evidence. PDP-02 remains unresolved pending independently reviewed scope/data and live verification; see PDP02_ROOT_CAUSE.md.

PDP-03: choose() previously clicked even an exclusively selected colour and lacked the PDP-02 popup guard. Saved popup DOM identifies the z-[9990] backdrop as Cookie consent (privacy heading, cookie policy, ?Ch?p nh?n t?t c??). choose() now invokes the existing identified-popup handler, which uses Selenium and waits until the backdrop disappears; it returns for an exclusively selected requested option. A late intercepted click triggers one bounded popup dismissal and a reacquired native click. Unknown persistent overlays still timeout with evidence. Size transitions, exclusive selection checks and all assertions are unchanged. No JS clicks or overlay removal.

## SKIP review

The claimed original 3 FAILED / 13 SKIPPED report is not the current primary report, which contains only PDP-01. Exact original skip reasons cannot be reconstructed from that file.

- PDP-04 requires verified sold-out URL/size; no new stock data invented.
- PDP-05 default colour/size selection makes the missing-selection precondition unreachable through the currently evidenced UI. Retain explicit SKIP; do not deselect through JS or replace its expected result with a successful Add.
- PDP-06 latest saved DOM DOES contain displayed `input#quantity-input`, aria-label ?S? l??ng?, value=1, type=text, and sibling buttons ?T?ng s? l??ng? / ?Gi?m s? l??ng?. Existing quantity locator already matches. Added only scoped sibling-button alternatives to plus/minus locators so the existing keyboard and +/- checks can run when present. No min/max/step attributes are published in this snapshot; do not infer a maximum or claim native numeric validation. 99999 remains unverified without a maximum; invalid text still requires actual block/adjustment/error evidence. A historical missing-input SKIP does not describe this latest DOM.
- PDP-07, PDP-08, PDP-10 remain Manual, byte-for-byte unchanged.
- PDP-09 requires real recommendation DOM; no new locator guessed.

## Verification and limits

- Compile every repository Python source in memory: PASS.
- Pytest collection through isolated PDP entry point: 16 tests, PASS.
- AST definition preservation and unchanged test/oracle comparison against this task baseline: PASS.
- Stored PDP-02 gallery replay (black timeout, gray after, beige after): preserves all recorded image sets, PASS; black mismatch retained.
- Three sequential runs of the unchanged PDP-01/02/03 tests: each 3 FAILED / 13 deselected, all stopped in driver.get() with Chrome 156.0.8078.74 `tab crashed`. These are browser/environment failures, not functional verdicts. No transition/size/quantity assertion was reached; repeated live stability and absence of cross-test UI effects remain UNVERIFIED.
- Debug launcher reuses workspace-cached ChromeDriver with the existing browser options, fresh browser per test and a bounded navigation timeout. It registers only a driver fixture, disables conftest/default report options, and writes separate logs. It does not rewrite existing CSV/HTML. Logs: `results/pdp_priority_fix/live_1.log` through `live_3.log`.
- No REG/LOG/shared fixture/reporting code edited. No existing file, function, class, test or data deleted. No Git repository available; unified source diff: `results/pdp_priority_fix/changes.diff`; baseline: `baseline.json` in that folder.
- Added debug runner: `results/pdp_priority_fix/run_live.py`; added this review document. The changes require live validation before any PASS claim.

## Rerun from project root

```powershell
python tools/run_pdp.py --collect-only
1..3 | ForEach-Object { python tools/run_pdp.py -k 'PDP_01 or PDP_02 or PDP_03' }
python tools/run_pdp.py -k 'PDP_05 or PDP_06'
python tools/run_pdp.py
```

Normal runner updates PDP reports only. To preserve all existing reports and reproduce this task's cached-driver diagnostic runs:

```powershell
python results/pdp_priority_fix/run_live.py
```
