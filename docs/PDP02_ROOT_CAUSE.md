# PDP-02 root cause review — 2026-11-03

Status: automation reader consistency repaired; image failure retained. Live reruns
blocked before navigation completed. No oracle changes approved or applied.

## Evidence and failure mechanism

Source: `results/pdp_evidence/pdp02_color_0_timeout.json` and matching PNG.
This is previously collected browser evidence, not a fresh observation today.

The gallery is a flex carousel (`pswp-gallery -ml-2 flex h-full`) inside
an overflow-hidden viewport. Slides have `flex-[0_0_100%]` and `pl-2`.
Thumbnail buttons are outside `#product-gallery`; a selected thumbnail lacks
the `opacity-50` token present on unselected thumbnails. Hidden slides remain
in the DOM and may have completed lazy loads; complete alone is not visibility.
The gallery transform is `matrix(1, 0, 0, 1, -554, 0)` with no running animations.

At the failed snapshot, viewport right edge = 738.4000091552734; the second
image starts at x = 738.0375366210938. Intersection width = 0.3624725341796875
CSS px; height = 805.4500122070312; area = 291.95350707974285 px².
Thus `area > 1` includes the neighbouring image even though the first image
occupies almost the entire viewport. This is deterministic in the stored
snapshot, not a loading timeout. Fractional layout makes this scope sensitive
to viewport dimensions, zoom and rounding.

Both images have `complete=true`, `naturalWidth=1100`, `loading=lazy`, empty
`srcset`, and currentSrc equals src. The neighbour belongs to the gallery:
IMG → A slide → DIV#product-gallery → overflow-hidden DIV. It is not the
FT_-80k promotion or a thumbnail. FT_-80k is absent from the current oracle.

All URLs below share:
`https://mcdn.coolmate.me/uploads/2026/10/21/`

| Color | Expected suffixes | Actual suffixes | Missing / extra |
|---|---|---|---|
| Đen V2 | `ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-denv2_3.jpg?aio=w-1100` | same plus `ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-denv2_1.jpg?aio=w-1100` | none / denv2_1 |
| Xám đậm V2 | xamdam-v2_3, xamdam-v2_9 | same | none / none |
| Be | be_4, be_10 | same | none / none |

The gray/beige stored snapshots have the same 0.3625 px neighbouring slide.
Their oracle includes it; the black oracle does not. The oracle is therefore
inconsistent for the current clipped-visible scope. Under a primary-active
scope gray/beige would instead contain extra expected images. Under a whole
library scope all three oracle sets would be incomplete. Those contracts
cannot be interchanged without reviewing expected results.

The existing `image_sources()` used Selenium displayed elements and loaded
properties sampled separately, whereas PDP-02 used one clipped-geometry
snapshot. This collector/test contract mismatch explains why recollection
can repeatedly produce an oracle that fails in the test.

## Criteria and changes

The repository does not contain the full Table 4.11. Its local checklist says
each colour must be selected exclusively and price/images/size set must match
an independently reviewed oracle; PDP-08 handles thumbnail navigation/zoom.
It does not specify whether PDP-02 compares the primary image, visible portion
of the carousel, or the full gallery. No stronger claim about Table 4.11 is made.

The existing PDP-02 scope is preserved pending that decision: every loaded
image with clipped area > 1 px², including edge slivers. Exact set equality
is unchanged. No URL normalization removes aio or any other query parameter;
both collector and test now use the same currentSrc-or-src rule from one
gallery snapshot. srcset candidates/data-src are diagnostics, not loaded URLs.
The no-argument image_sources contract remains unchanged for PDP-01.

Changed production files:

- pages/pdp_support.py: optional atomic PDP-02 image reader; visible fraction
  added as diagnostics only. No geometry threshold changed.
- tools/inspect_pdp_variants.py: same reader and gallery snapshot as PDP-02;
  records contract identifier and geometry for independent review.
- tests/test_chi_tiet_san_pham.py: PDP-02 only; if the first colour is selected,
  verify another colour first, then verify the original full sequence. Unique
  evidence paths preserve both visits. Failures include expected/actual,
  missing/extra, primary image, clipped widths and gallery state.

ProductPage was fully read; no change was needed. No files/functions/classes
were removed. REG/LOG and other PDP test functions were not edited. Existing
price, colour, URL and size assertions are unchanged. No JS carousel reset,
fixed sleep, weaker image comparison or automatic oracle update was added.

## Verification

- Python compilation of all three changed files: PASS.
- AST comparison: no definitions removed; every test function except PDP-02
  is identical to its pre-edit AST.
- Oracle byte comparison: identical to pre-edit backup.
- Replay of all three saved gallery snapshots through the shared reader:
  preserves actual sets exactly; black still mismatches, gray/beige match.
  This verifies reader consistency only, not current website behavior.
- Diff: results/pdp02_root_cause/changes.diff. Git unavailable: directory
  has no Git repository.
- Initial standard driver startup failed at webdriver_manager chmod with
  WinError 5 outside workspace. A debug-only launcher reuses the existing
  workspace chromedriver without changing utils/driver_factory.py.
- Two fresh browser attempts (headed and headless) failed in driver.get with
  `WebDriverException: tab crashed`, Chrome 156.0.8078.74. Neither reached
  colour selection. Logs: results/pdp02_root_cause/live_run1.log and
  live_run2.log. Full transition and repeated-run stability remain unverified.

The old black screenshot shows a black jacket and Đen V2 selected, with the
expected price. No website wrong-colour defect is established. A future
wrong-colour UI must remain FAILED with its screenshot; do not change oracle
based on the failing UI alone.

## Review required and rerun

Do not append denv2_1 just to pass: it encodes a subpixel edge artifact into
the oracle. Confirm the intended image scope from the original Table 4.11
before changing oracle or excluding that edge. If clipped-visible scope is
explicitly approved, black is missing the full denv2_1 URL above in this
snapshot; independently recapture all colours at the agreed viewport first.
If primary-active scope is approved, update reader and all three oracle
entries together only after independent visual review.

Normal rerun, twice, from project root:

```powershell
python tools/run_pdp.py -k PDP_02
python tools/run_pdp.py -k PDP_02
```

Local cached-driver debug fallback (same test and assertions):

```powershell
python results/pdp02_root_cause/run_local_driver.py repeat1.log
python results/pdp02_root_cause/run_local_driver.py repeat2.log
```

With default Đen V2 selected, each run verifies departure to Xám đậm V2,
then Đen V2 → Xám đậm V2 → Be, retaining every failed transition.
