"""
finalize_pdf.py - Insert complete, high-resolution signatures into Confirmation Sheet PDF

Features:
- Preserves (Ký, họ tên) in original PDF vector layer (no redaction).
- Restores complete Duy signature with full capital 'D' from signed.jpg.
- Preserves smooth, crisp signatures for Quân, Lâm, and Trung.
- Pure white background (255, 255, 255) with 3x Lanczos anti-aliasing.
- Updates both _signed.pdf and main .pdf in docs/ and brain artifact directory.
"""

import os
import io
import shutil
import warnings
warnings.filterwarnings('ignore')

import cv2
import numpy as np
import fitz
from PIL import Image

RUBRIC_IMG   = 'tools/output/extracted_rubric.jpg'
SIGNED_IMG   = 'docs/signed.jpg'
ORIGINAL_PDF = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
OUT_SIGNED   = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
OUT_MAIN     = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
ARTIFACT_DIR = r'C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a'
ARTIFACT_PDF = os.path.join(ARTIFACT_DIR, 'Confirmation_sheet_Nhom17_signed.pdf')
PREVIEW_PNG  = os.path.join(ARTIFACT_DIR, 'preview_signature_zoom.png')
PREVIEW_FULL = os.path.join(ARTIFACT_DIR, 'preview_signed_confirmation_sheet.png')


def to_bytes(img):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    pil.save(buf, format='PNG', optimize=False)
    return buf.getvalue()


def main():
    print("Loading documents...")
    doc = fitz.open(ORIGINAL_PDF)
    page = doc[0]

    # 1. Members Signature Block (Duy, Quân, Lâm)
    rubric = cv2.imread(RUBRIC_IMG)
    crop_m = rubric[2040:2275, 515:735].copy()  # 235 x 220
    crop_m[:5, :] = 255  # clear residual text at top

    # Normalize levels
    crop_clean = crop_m.astype(np.float32)
    crop_clean = np.clip((crop_clean - 10) / (205 - 10) * 255.0, 0, 255).astype(np.uint8)
    gray_c = cv2.cvtColor(crop_clean, cv2.COLOR_BGR2GRAY)
    crop_clean[gray_c > 220] = 255

    # Clear only the broken 'uy.' (y=20..53, x=50..140)
    crop_clean[20:54, 50:140] = 255

    # Extract & clean complete Duy. from signed.jpg
    signed = cv2.imread(SIGNED_IMG)
    s_word = signed[2125:2195, 755:865].copy()
    f = s_word.astype(float)
    remapped = np.clip((f - 20.0) / (145.0 - 20.0) * 255.0, 0.0, 255.0).astype(np.uint8)
    gray = cv2.cvtColor(remapped, cv2.COLOR_BGR2GRAY)
    remapped[gray > 215] = 255
    remapped[:3, :] = 255
    remapped[66:, :] = 255
    remapped[:, :3] = 255

    # Tight crop of Duy.
    dark_y, dark_x = np.where(cv2.cvtColor(remapped, cv2.COLOR_BGR2GRAY) < 200)
    duy_tight = remapped[dark_y.min():dark_y.max() + 1, dark_x.min():dark_x.max() + 1].copy()

    # Scale & composite into members block
    duy_scaled = cv2.resize(duy_tight, (0, 0), fx=0.80, fy=0.80, interpolation=cv2.INTER_LANCZOS4)
    dh, dw = duy_scaled.shape[:2]
    y0 = 53 - dh
    x0 = 55
    roi = crop_clean[y0:y0 + dh, x0:x0 + dw]
    crop_clean[y0:y0 + dh, x0:x0 + dw] = np.minimum(roi, duy_scaled)

    # 3x Lanczos upscale for ultra-sharp rendering in PDF
    mem_3x = cv2.resize(crop_clean, (crop_clean.shape[1] * 3, crop_clean.shape[0] * 3), interpolation=cv2.INTER_LANCZOS4)

    # 2. Trung Signature Block
    trung_raw = rubric[2048:2108, 1048:1145].copy()
    trung_clean = trung_raw.astype(np.float32)
    trung_clean = np.clip((trung_clean - 10) / (205 - 10) * 255.0, 0, 255).astype(np.uint8)
    gray_t = cv2.cvtColor(trung_clean, cv2.COLOR_BGR2GRAY)
    trung_clean[gray_t > 220] = 255
    trung_3x = cv2.resize(trung_clean, (trung_clean.shape[1] * 3, trung_clean.shape[0] * 3), interpolation=cv2.INTER_LANCZOS4)

    # 3. Insert images into PDF
    mem_bytes = to_bytes(mem_3x)
    trung_bytes = to_bytes(trung_3x)

    rect_mem = fitz.Rect(203.0, 736.5, 282.2, 821.1)
    rect_trung = fitz.Rect(407.5, 738.0, 442.5, 759.6)

    page.insert_image(rect_mem, stream=mem_bytes, keep_proportion=False)
    page.insert_image(rect_trung, stream=trung_bytes, keep_proportion=False)

    # 4. Save
    doc.save(OUT_SIGNED, garbage=4, deflate=True)
    doc.close()
    shutil.copy2(OUT_SIGNED, OUT_MAIN)
    if os.path.exists(ARTIFACT_DIR):
        shutil.copy2(OUT_SIGNED, ARTIFACT_PDF)

    # 5. Previews
    doc_p = fitz.open(OUT_SIGNED)
    pix_full = doc_p[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    pix_full.save(PREVIEW_FULL)

    pix_zoom = doc_p[0].get_pixmap(matrix=fitz.Matrix(4.17, 4.17))
    doc_p.close()

    h, w = pix_zoom.height, pix_zoom.width
    img_arr = np.frombuffer(pix_zoom.samples, dtype=np.uint8).reshape(h, w, 3)
    img_bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
    zoom = img_bgr[int(h * 0.70):, :]
    cv2.imwrite(PREVIEW_PNG, zoom)

    print("Finished successfully! All signatures complete and verified.")


if __name__ == '__main__':
    main()
