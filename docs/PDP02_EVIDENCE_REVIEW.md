# PDP-02 evidence review - 2026-11-03

Status: BLOCKED on gallery verification. No oracle created; no PASS claimed.

Reviewed: the three JSON files below, matching PNG screenshots, tests/test_chi_tiet_san_pham.py, docs/PDP_MANUAL_TESTS.md, and pages/pdp_support.py. All three JSON files parse successfully.

## Đen V2

Evidence: `results/pdp_evidence/manual_20261103_104921_830710.json` and matching PNG.

URL: https://www.coolmate.me/product/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026?color=den-v2

Color and size URLs match. Exactly this color is selected; panel label and visible jacket color agree with the screenshot.
Price recorded in JSON: `899.000đ`.
Sizes M/L/XL/2XL/3XL all have disabled=false; only M is selected. Button DOM shows no disabled marker.

Captured image sources:

- https://mcdn.coolmate.me/uploads/2026/10/21/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-denv2_3.jpg?aio=w-1100
- https://mcdn.coolmate.me/uploads/2026/11/02/FT_-80k.jpg?aio=w-750

## Xám đậm V2

Evidence: `results/pdp_evidence/manual_20261103_103926_262095.json` and matching PNG.

URL: https://www.coolmate.me/product/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026?color=xam-dam-v2

Color and size URLs match. Exactly this color is selected; panel label and visible jacket color agree with the screenshot.
Price recorded in JSON: `899.000đ`.
Sizes M/L/XL/2XL/3XL all have disabled=false; only M is selected. Button DOM shows no disabled marker.

Captured image sources:

- https://mcdn.coolmate.me/uploads/2026/10/21/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-xamdam-v2_3.jpg?aio=w-1100
- https://mcdn.coolmate.me/uploads/2026/10/21/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-xamdam-v2_9.jpg?aio=w-1100
- https://mcdn.coolmate.me/uploads/2026/11/02/FT_-80k.jpg?aio=w-750

## Be

Evidence: `results/pdp_evidence/manual_20261103_103942_294190.json` and matching PNG.

URL: https://www.coolmate.me/product/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026?color=be

Color and size URLs match. Exactly this color is selected; panel label and visible jacket color agree with the screenshot.
Price recorded in JSON: `899.000đ`.
Sizes M/L/XL/2XL/3XL all have disabled=false; only M is selected. Button DOM shows no disabled marker.

Captured image sources:

- https://mcdn.coolmate.me/uploads/2026/10/21/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-be_4.jpg?aio=w-1100
- https://mcdn.coolmate.me/uploads/2026/10/21/ao-phao-day-ultrawarm-puffer-co-mu-ii-new-2026-be_10.jpg?aio=w-1100
- https://mcdn.coolmate.me/uploads/2026/11/02/FT_-80k.jpg?aio=w-750

## Verification required

- Every image set contains FT_-80k.jpg (full URL above), suspected voucher/banner. Its contents and gallery membership are unverified. Do not treat it as a product image or silently remove it to force PASS.
- The JSON files contain variant panel HTML, not gallery DOM or image ancestors. Matching color tokens in filenames do not establish gallery membership.
- Screenshots show matching jacket colors and multiple thumbnails. JSON contains only 1 black jacket image, 2 gray images, and 2 beige images. Confirm the complete, stable currentSrc set at the test viewport and scroll position, including lazy loading. Thumbnail count alone does not establish missing images because the helper reads displayed, loaded images.
- Only the black screenshot shows the price; gray/beige screenshots are scrolled below it. Confirm their prices visually.
- The helper has a broad image fallback and a banner/voucher string filter that does not recognize the filename FT_-80k.jpg. No helper changes were made.
- Web access to the Be product page and FT_-80k image failed during review.

Collect gallery DOM, including ancestor containers and currentSrc for each image, and visually verify FT_-80k and all jacket images. Recollect stable variants at the test viewport/scroll position with `python tools/inspect_pdp_variants.py`.

## Oracle and rerun

Required schema: url; colors keyed by all three exact labels; each color has price, images, and sizes mapping M/L/XL/2XL/3XL to boolean disabled values.

The .env entry remains PDP_VARIANT_EXPECTATIONS=data/pdp_variant_expectations.json. No REG, LOG, PDP-01, PDP-03 code or test reports were changed.

After independent verification and creation of the oracle, run from project root:

```powershell
python -m json.tool data/pdp_variant_expectations.json > $null
python tools/run_pdp.py -k PDP_02 -x
```

Until then, the missing oracle and FileNotFoundError remain unresolved. Git diff is unavailable because this directory is not a Git repository. The only change in this review is this new document.
