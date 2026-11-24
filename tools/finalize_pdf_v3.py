"""
finalize_pdf_v3.py - Clean signature extraction & PDF insertion
Sources:
  - Rubric: tools/output/extracted_rubric.jpg (1653x2339)
  - Original blank PDF: docs/260903..._(4)_original.pdf
Output:
  - docs/260903..._(4)_signed.pdf
  - docs/260903..._(4).pdf
  - Artifact copy

Key findings from analysis:
  - Members column signatures: x=[560..680], y=[2060..2270] in rubric
  - Trung signature: x=[1053..1140], y=[2050..2110] in rubric
  - (Ky, ho ten) text for members: y=2022..2042, x=610..730 (Thanh vien col)
  - (Ky, ho ten) text for Trung: y=2022..2042, x=1110..1260
  - (Ky, ho ten) text for Huong dan: y=2022..2042, x=400..490
"""

import cv2
import numpy as np
import fitz  # PyMuPDF
import shutil
import os
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────────
RUBRIC_IMG   = "tools/output/extracted_rubric.jpg"
ORIGINAL_PDF = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf"
OUT_SIGNED   = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf"
OUT_MAIN     = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf"
ARTIFACT_DIR = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
ARTIFACT_PDF = os.path.join(ARTIFACT_DIR, "Confirmation_sheet_Nhom17_signed.pdf")
PREVIEW_PNG  = os.path.join(ARTIFACT_DIR, "preview_signature_zoom.png")


def clean_signature(crop_bgr, black_point=10, white_point=215, upscale=2):
    """
    Normalize levels so near-white becomes 255, then optionally upscale.
    Returns BGR image with pure white background.
    """
    img = crop_bgr.astype(np.float32)
    # Levels: remap [black_point..white_point] -> [0..255]
    img = np.clip((img - black_point) / (white_point - black_point) * 255, 0, 255)
    img = img.astype(np.uint8)
    # Force any pixel > 230 to pure white (kill paper grain)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img[gray > 230] = 255
    if upscale > 1:
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * upscale, h * upscale), interpolation=cv2.INTER_LANCZOS4)
    return img


def img_to_png_bytes(bgr_img):
    """Convert BGR numpy array to PNG bytes."""
    pil = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
    import io
    buf = io.BytesIO()
    pil.save(buf, format="PNG", optimize=False, compress_level=1)
    return buf.getvalue()


# ── 1. Load rubric ─────────────────────────────────────────────────────────────
print("Loading rubric scan...")
rubric = cv2.imread(RUBRIC_IMG)
assert rubric is not None, f"Cannot read {RUBRIC_IMG}"
print(f"Rubric shape: {rubric.shape}")  # expected (2339, 1653, 3)

rubric_work = rubric.copy()

# ── 2. White-out ONLY the printed "(Ky, ho ten)" text – NOT signatures ────────
# Members column (Thanh vien nhom): (Ky, ho ten) at y=2022..2042, x=605..735
rubric_work[2020:2045, 605:740] = 255
# Trung column: (Ky, ho ten) at y=2022..2042, x=1105..1265
rubric_work[2020:2045, 1100:1270] = 255
# Huong dan column: (Ky, ho ten) at y=2022..2042, x=395..495
rubric_work[2020:2045, 390:500] = 255

# ── 3. Extract member signatures crop ─────────────────────────────────────────
# From analysis: Duy's signature starts at y=2060 (D loop),
# Full member block goes to y~2270. X range: 520..720
# Give a wide margin: x=510..730, y=2020..2275
# y start at 2020 so we capture any top elements, we already cleared (Ky, ho ten)
crop_members = rubric_work[2020:2278, 510:740].copy()
print(f"Members crop shape: {crop_members.shape}")

# ── 4. Extract Trung signature crop ───────────────────────────────────────────
# From analysis: Trung at y=2050..2115, x=1053..1140
# Give margin: y=2040..2120, x=1040..1155
crop_trung = rubric_work[2040:2125, 1040:1160].copy()
print(f"Trung crop shape: {crop_trung.shape}")

# ── 5. Clean and upscale ──────────────────────────────────────────────────────
sig_members = clean_signature(crop_members, black_point=8, white_point=200, upscale=3)
sig_trung   = clean_signature(crop_trung,   black_point=8, white_point=200, upscale=3)

# Save debug crops
cv2.imwrite("tools/output/debug_members_crop_v3.jpg", sig_members)
cv2.imwrite("tools/output/debug_trung_crop_v3.jpg", sig_trung)
print("Saved debug crops")

# ── 6. Open original blank PDF ────────────────────────────────────────────────
print(f"Opening original PDF: {ORIGINAL_PDF}")
doc = fitz.open(ORIGINAL_PDF)
page = doc[0]
page_rect = page.rect
print(f"Page rect: {page_rect}")  # expected ~595x842 pt

# ── 7. Redact "(Ky, ho ten)" from PDF vector text layer ──────────────────────
# Search for all variants of this text and redact
search_terms = ["(Ký, họ tên)", "(Ký,họ tên)", "(Ky, ho ten)", "Ký, họ tên"]
for term in search_terms:
    rects = page.search_for(term)
    for r in rects:
        # Expand rect slightly to cover full text
        expanded = fitz.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        page.add_redact_annot(expanded, fill=(1, 1, 1))
        print(f"  Redact '{term}' at {r}")
page.apply_redactions()
print("Redactions applied")

# ── 8. Insert signatures into PDF ─────────────────────────────────────────────
# PDF page is 595.08 x 842.04 pt (A4)
# From the PDF structure, the signature zone is in the bottom section.
# 
# Trung column center: approximately x=424 pt (right side)
# Members column center: approximately x=240 pt (middle)
# Signature top: approximately y=730 pt
#
# Rubric is 1653px wide = 595pt => scale = 595/1653 = 0.3600 pt/px
# 
# Members crop: x=510..740 px => x_pt = 510*0.360=183.6 .. 740*0.360=266.4
#               y=2020..2278 px => y_pt = 2020*0.360=727.2 .. 2278*0.360=820.1
# Trung crop:   x=1040..1160 px => x_pt = 374.4..417.6
#               y=2040..2125 px => y_pt = 734.4..765.0

scale = 595.08 / 1653.0

members_x0 = 510 * scale
members_x1 = 740 * scale
members_y0 = 2020 * scale
members_y1 = 2278 * scale
rect_members = fitz.Rect(members_x0, members_y0, members_x1, members_y1)

trung_x0 = 1040 * scale
trung_x1 = 1160 * scale
trung_y0 = 2040 * scale
trung_y1 = 2125 * scale
rect_trung = fitz.Rect(trung_x0, trung_y0, trung_x1, trung_y1)

print(f"Members rect (pt): {rect_members}")
print(f"Trung rect (pt):   {rect_trung}")

# Insert as images
members_png = img_to_png_bytes(sig_members)
trung_png   = img_to_png_bytes(sig_trung)

page.insert_image(rect_members, stream=members_png, keep_proportion=False)
page.insert_image(rect_trung,   stream=trung_png,   keep_proportion=False)
print("Images inserted")

# ── 9. Save PDF outputs ───────────────────────────────────────────────────────
doc.save(OUT_SIGNED, garbage=4, deflate=True)
doc.close()
shutil.copy2(OUT_SIGNED, OUT_MAIN)
shutil.copy2(OUT_SIGNED, ARTIFACT_PDF)
print(f"Saved: {OUT_SIGNED}")
print(f"Copied to: {OUT_MAIN}")
print(f"Copied to: {ARTIFACT_PDF}")

# ── 10. Generate 300 DPI preview ──────────────────────────────────────────────
print("Generating preview...")
doc2 = fitz.open(OUT_SIGNED)
page2 = doc2[0]
# Render at 300 DPI (scale=300/72 ≈ 4.167)
mat = fitz.Matrix(4.0, 4.0)
pix = page2.get_pixmap(matrix=mat, alpha=False)
doc2.close()

# Crop bottom portion (signature area only) for preview
h, w = pix.height, pix.width
img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w, 3)
img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)

# Bottom 35% of page contains signatures
bottom_start = int(h * 0.70)
preview = img_bgr[bottom_start:, :]
cv2.imwrite(PREVIEW_PNG, preview)
print(f"Preview saved: {PREVIEW_PNG}")
print("DONE!")
