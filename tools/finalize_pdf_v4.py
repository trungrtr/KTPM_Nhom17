"""
finalize_pdf_v4.py - Chính xác tọa độ, giữ nguyên (Ký, họ tên) trong PDF gốc

PDF TEXT POSITIONS (from actual PDF extraction):
  'Hướng dẫn'       x=[134.7..177.2], center=156
  'Thành viên nhóm' x=[210.0..274.9], center=242
  'Trưởng nhóm'     x=[399.4..451.1], center=425
  '(Ký, họ tên)' TV bbox=[222.1, 727.7, 262.6, 735.6]  <- signature zone starts below y=735
  '(Ký, họ tên)' TN bbox=[404.9, 727.7, 445.3, 735.6]
  'Đào Quang Trung'  bbox=[392.2, 765.7, 457.9, 773.6]  <- signature must be above 765

RUBRIC SIGNATURE COORDS (1653x2339 pixels, scale=595/1653=0.3600 pt/px):
  Members (all 3): x=[530..720], y=[2072..2267]  
    -> PDF: x=[190.8..259.2], y=[745.9..816.1]
  Trung: x=[1050..1145], y=[2048..2110]
    -> PDF: x=[378.0..412.2], y=[737.3..759.6]

STRATEGY:
  - Use rubric as source (clean, complete signatures)
  - DO NOT redact (Ký, họ tên) - keep original PDF text intact
  - Insert member signatures image at exact position below (Ký, họ tên)
  - Insert Trung signature image at exact position below (Ký, họ tên)
"""

import cv2
import numpy as np
import fitz  # PyMuPDF
import shutil
import os
import io
import warnings
warnings.filterwarnings('ignore')
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────────
RUBRIC_IMG   = "tools/output/extracted_rubric.jpg"
ORIGINAL_PDF = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf"
OUT_SIGNED   = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf"
OUT_MAIN     = "docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf"
ARTIFACT_DIR = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
ARTIFACT_PDF = os.path.join(ARTIFACT_DIR, "Confirmation_sheet_Nhom17_signed.pdf")
PREVIEW_PNG  = os.path.join(ARTIFACT_DIR, "preview_signature_zoom.png")


def clean_signature(crop_bgr, black_point=12, white_point=210, upscale=3):
    """Normalize + upscale. Returns BGR with pure white background."""
    img = crop_bgr.astype(np.float32)
    img = np.clip((img - black_point) / (white_point - black_point) * 255, 0, 255)
    img = img.astype(np.uint8)
    # Snap near-white to pure white
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img[gray > 225] = 255
    if upscale > 1:
        h, w = img.shape[:2]
        img = cv2.resize(img, (w * upscale, h * upscale), interpolation=cv2.INTER_LANCZOS4)
    return img


def to_png_bytes(bgr_img):
    pil = Image.fromarray(cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil.save(buf, format="PNG", optimize=False, compress_level=1)
    return buf.getvalue()


# ── 1. Load rubric ─────────────────────────────────────────────────────────────
print("Loading rubric scan...")
rubric = cv2.imread(RUBRIC_IMG)
assert rubric is not None
print(f"Rubric shape: {rubric.shape}")  # (2339, 1653, 3)

# Scale factor: rubric 1653px wide = 595pt
SCALE = 595.0 / 1653.0
print(f"Scale: {SCALE:.5f} pt/px")

# ── 2. Extract members signatures crop from rubric ────────────────────────────
# From pixel analysis:
#   Duy: y=2072..2119, x=558..674
#   Quan: y=2132..2183, x=536..677  
#   Lam: y=2220..2267, x=530..719
#   Full block: x=525..725, y=2065..2275 (with margin)
MEM_Y0, MEM_Y1 = 2065, 2275
MEM_X0, MEM_X1 = 522, 728

crop_members = rubric[MEM_Y0:MEM_Y1, MEM_X0:MEM_X1].copy()
print(f"Members crop: {crop_members.shape} (from rubric y={MEM_Y0}..{MEM_Y1}, x={MEM_X0}..{MEM_X1})")

# ── 3. Extract Trung signature crop from rubric ───────────────────────────────
# From pixel analysis:
#   Trung: y=2048..2101, x=1053..1140
#   Add margin: y=2043..2110, x=1048..1145
TRG_Y0, TRG_Y1 = 2043, 2112
TRG_X0, TRG_X1 = 1046, 1150

crop_trung = rubric[TRG_Y0:TRG_Y1, TRG_X0:TRG_X1].copy()
print(f"Trung crop: {crop_trung.shape} (from rubric y={TRG_Y0}..{TRG_Y1}, x={TRG_X0}..{TRG_X1})")

# ── 4. Clean and upscale ──────────────────────────────────────────────────────
sig_members = clean_signature(crop_members, black_point=10, white_point=205, upscale=3)
sig_trung   = clean_signature(crop_trung,   black_point=10, white_point=205, upscale=3)

# Save debug
cv2.imwrite("tools/output/v4_members_crop.jpg", sig_members, [cv2.IMWRITE_JPEG_QUALITY, 95])
cv2.imwrite("tools/output/v4_trung_crop.jpg", sig_trung, [cv2.IMWRITE_JPEG_QUALITY, 95])
print("Saved debug crops")

# ── 5. Calculate EXACT PDF insertion rects ────────────────────────────────────
# PDF page: 595 x 842 pt
# 
# Members column:
#   - '(Ký, họ tên)' label ends at y=735.6 pt
#   - 'Đào Quang Trung' printed text at y=765.7 pt
#   - Signatures should fit between y=737 and y=820 (bottom margin)
#   - Thành viên nhóm center x ≈ 242 pt
#   - Rubric member sigs span from x=MEM_X0..MEM_X1 in rubric
#   - In PDF: x0 = MEM_X0 * SCALE = 188.1, x1 = MEM_X1 * SCALE = 262.3
#   - In PDF: y0 = MEM_Y0 * SCALE = 743.4, y1 = MEM_Y1 * SCALE = 819.0
#
# Trung column:
#   - '(Ký, họ tên)' for Trung ends at y=735.6
#   - 'Đào Quang Trung' at y=765.7 -> Trung sig must end before 762
#   - Trưởng nhóm center x ≈ 425 pt
#   - Rubric Trung spans x=TRG_X0..TRG_X1
#   - In PDF: x0 = 1046*SCALE = 376.6, x1 = 1150*SCALE = 414.1
#   - In PDF: y0 = 2043*SCALE = 735.5, y1 = 2112*SCALE = 760.3

# Members rect (keep (Ky, ho ten) text, signatures go below y=736)
rect_members = fitz.Rect(
    MEM_X0 * SCALE,   # x0 = 188.0
    MEM_Y0 * SCALE,   # y0 = 743.4  (below (Ky, ho ten) which ends at 735.6)
    MEM_X1 * SCALE,   # x1 = 262.3
    MEM_Y1 * SCALE    # y1 = 819.0
)

# Trung rect  
rect_trung = fitz.Rect(
    TRG_X0 * SCALE,   # x0 = 376.6
    TRG_Y0 * SCALE,   # y0 = 735.5  (below (Ky, ho ten))
    TRG_X1 * SCALE,   # x1 = 414.1
    TRG_Y1 * SCALE    # y1 = 760.3
)

print(f"Members rect (pt): x={rect_members.x0:.1f}..{rect_members.x1:.1f}, y={rect_members.y0:.1f}..{rect_members.y1:.1f}")
print(f"Trung rect   (pt): x={rect_trung.x0:.1f}..{rect_trung.x1:.1f}, y={rect_trung.y0:.1f}..{rect_trung.y1:.1f}")

# Verify positions make sense:
print(f"\nVerification:")
print(f"  (Ky, ho ten) TV ends at y=735.6 -> Members sig starts at y={rect_members.y0:.1f} ✓" if rect_members.y0 >= 736 else "  WARNING: Members sig overlaps (Ky, ho ten)!")
print(f"  Dao Quang Trung at y=765.7 -> Trung sig ends at y={rect_trung.y1:.1f} ✓" if rect_trung.y1 <= 764 else f"  NOTE: Trung sig y1={rect_trung.y1:.1f} vs text at 765.7 - close!")

# ── 6. Open original PDF and insert images (NO REDACTION - keep (Ky, ho ten)) ─
print(f"\nOpening original PDF...")
doc = fitz.open(ORIGINAL_PDF)
page = doc[0]
print(f"Page rect: {page.rect}")

# Insert images - NO redaction of (Ky, ho ten)!
members_png = to_png_bytes(sig_members)
trung_png   = to_png_bytes(sig_trung)

page.insert_image(rect_members, stream=members_png, keep_proportion=False)
page.insert_image(rect_trung,   stream=trung_png,   keep_proportion=False)
print("Images inserted (kept (Ky, ho ten) text intact)")

# ── 7. Save PDF ───────────────────────────────────────────────────────────────
doc.save(OUT_SIGNED, garbage=4, deflate=True)
doc.close()
shutil.copy2(OUT_SIGNED, OUT_MAIN)
shutil.copy2(OUT_SIGNED, ARTIFACT_PDF)
print(f"Saved: {OUT_SIGNED}")
print(f"Copied: {OUT_MAIN}")
print(f"Copied: {ARTIFACT_PDF}")

# ── 8. Generate preview (300 DPI bottom section) ──────────────────────────────
print("Generating 300 DPI preview...")
doc2 = fitz.open(OUT_SIGNED)
page2 = doc2[0]
mat = fitz.Matrix(4.17, 4.17)   # ~300 DPI (72*4.17=300)
pix = page2.get_pixmap(matrix=mat, alpha=False)
doc2.close()

h, w = pix.height, pix.width
img_arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w, 3)
img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)

# Crop bottom 35% (signature zone)
bottom_start = int(h * 0.70)
preview = img_bgr[bottom_start:, :]
cv2.imwrite(PREVIEW_PNG, preview)
print(f"Preview saved: {PREVIEW_PNG}")
print("DONE!")
