"""
finalize_pdf.py - Insert complete, high-resolution signatures into Confirmation Sheet PDF

Key features:
1. Preserves original vector text '(Ký, họ tên)' and 'Đào Quang Trung' (no redaction or overwriting).
2. Duy's signature is 100% complete with full capital 'D' loop and 'mạc tiến Duy' extracted from signed.jpg.
3. Quân and Lâm are completely preserved with full rightward underline flourish and natural handwriting.
4. Trung's signature is cleaned of any scan specks and centered above 'Đào Quang Trung'.
5. 3x Lanczos upscaling with anti-aliased RGBA transparency for ultra-sharp vector-like insertion.
6. Pure white background (255, 255, 255) with zero gray boxes, shadows, or halos.
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

RUBRIC_PDF   = 'docs/Rubric_HopTacNhom_Nhom17_Signed (1).pdf'
SIGNED_IMG   = 'docs/signed.jpg'
ORIGINAL_PDF = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
OUT_SIGNED   = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
OUT_MAIN     = 'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
ARTIFACT_DIR = r'C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a'
ARTIFACT_PDF = os.path.join(ARTIFACT_DIR, 'Confirmation_sheet_Nhom17_signed.pdf')
PREVIEW_PNG  = os.path.join(ARTIFACT_DIR, 'preview_signature_zoom.png')
PREVIEW_DUY  = os.path.join(ARTIFACT_DIR, 'preview_duy_zoom.png')
PREVIEW_FULL = os.path.join(ARTIFACT_DIR, 'preview_signed_confirmation_sheet.png')


def clean_photo_crop(img, kernel_size=35, bg_thresh=220, ink_darken=1.15):
    """Normalize illumination from photo crop and convert background to pure white with anti-aliasing."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bg_gray = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)
    norm_gray = np.clip(gray.astype(float) / (bg_gray.astype(float) + 1e-5) * 255.0, 0, 255)

    cleaned_channels = []
    for c in range(3):
        ch = img[:, :, c]
        bg = cv2.morphologyEx(ch, cv2.MORPH_DILATE, kernel)
        norm = np.clip(ch.astype(float) / (bg.astype(float) + 1e-5) * 255.0, 0, 255)
        cleaned_channels.append(norm)
    norm_bgr = cv2.merge(cleaned_channels)

    ink_thresh = 150.0
    alpha = np.clip((norm_gray - ink_thresh) / (bg_thresh - ink_thresh), 0.0, 1.0)
    alpha = alpha * alpha * (3 - 2 * alpha)

    result = np.zeros_like(norm_bgr, dtype=np.uint8)
    for c in range(3):
        ink_ch = np.clip(norm_bgr[:, :, c] * (1.0 / ink_darken), 0, 255)
        blended = ink_ch * (1.0 - alpha) + 255.0 * alpha
        result[:, :, c] = np.clip(blended, 0, 255).astype(np.uint8)
    return result


def make_rgba(img_bgr, bg_cutoff=215.0):
    """Upscale 3x Lanczos and generate smooth anti-aliased RGBA transparency."""
    h, w = img_bgr.shape[:2]
    up = cv2.resize(img_bgr, (w * 3, h * 3), interpolation=cv2.INTER_LANCZOS4)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)

    alpha = np.clip((255.0 - gray.astype(float)) / (255.0 - bg_cutoff), 0.0, 1.0)
    alpha = (alpha * alpha * (3 - 2 * alpha) * 255.0).astype(np.uint8)

    b, g, r = cv2.split(up)
    rgba = cv2.merge([b, g, r, alpha])

    _, buf = cv2.imencode('.png', rgba)
    return buf.tobytes()


def main():
    print("1. Extracting base scans and photos...")
    doc_r = fitz.open(RUBRIC_PDF)
    rubric_scan = None
    for img_info in doc_r[0].get_images():
        base_img = doc_r.extract_image(img_info[0])
        rubric_scan = cv2.imdecode(np.frombuffer(base_img['image'], np.uint8), cv2.IMREAD_COLOR)
        break
    doc_r.close()

    signed_photo = cv2.imread(SIGNED_IMG)

    print("2. Extracting and cleaning Duy signature from signed photo...")
    # Duy complete signature in signed photo: y=2129..2260, x=725..990
    duy_crop = signed_photo[2129:2260, 725:990].copy()
    duy_clean = clean_photo_crop(duy_crop, kernel_size=35, bg_thresh=220, ink_darken=1.15)

    # Tight crop around Duy ink
    gray_d = cv2.cvtColor(duy_clean, cv2.COLOR_BGR2GRAY)
    dark_y, dark_x = np.where(gray_d < 220)
    duy_tight = duy_clean[dark_y.min():dark_y.max() + 1, dark_x.min():dark_x.max() + 1]

    print("3. Extracting members block (Quan, Lam) with full flourish...")
    # Full members crop from rubric scan: y=2040..2278, x=515..780
    full_crop_m = rubric_scan[2040:2278, 515:780].copy()
    m_clean = full_crop_m.astype(np.float32)
    m_clean = np.clip((m_clean - 10) / (205 - 10) * 255.0, 0, 255).astype(np.uint8)
    gray_m = cv2.cvtColor(m_clean, cv2.COLOR_BGR2GRAY)
    m_clean[gray_m > 220] = 255

    # Completely wipe the old truncated Duy region (y=0..82)
    m_clean[0:82, :] = 255

    # Scale Duy proportionally to fit slot (target height 76 px, matching Quan and Lam)
    th, tw = duy_tight.shape[:2]
    target_h = 76
    scale = target_h / th
    target_w = int(tw * scale)
    duy_scaled = cv2.resize(duy_tight, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

    # Position Duy centered horizontally in the block
    y_offset = 3
    x_offset = 50
    roi = m_clean[y_offset:y_offset + target_h, x_offset:x_offset + target_w]
    m_clean[y_offset:y_offset + target_h, x_offset:x_offset + target_w] = np.minimum(roi, duy_scaled)

    print("4. Extracting and cleaning Trung signature...")
    trung_raw = rubric_scan[2048:2108, 1048:1145].copy()
    trung_clean = trung_raw.astype(np.float32)
    trung_clean = np.clip((trung_clean - 10) / (205 - 10) * 255.0, 0, 255).astype(np.uint8)
    gray_t = cv2.cvtColor(trung_clean, cv2.COLOR_BGR2GRAY)
    trung_clean[gray_t > 220] = 255
    # Clear residual scan specks at top (rows 0..5)
    trung_clean[0:6, :] = 255

    print("5. Generating high-resolution RGBA streams...")
    mem_png_bytes = make_rgba(m_clean)
    trung_png_bytes = make_rgba(trung_clean)

    print("6. Inserting signatures into original Confirmation Sheet PDF...")
    doc = fitz.open(ORIGINAL_PDF)
    page = doc[0]

    # Calculate exact rects
    # Members: width 94.2, height 84.6, centered at x=241.0, y below (Ký, họ tên) at y=736.5
    rect_mem = fitz.Rect(193.9, 736.5, 288.1, 821.1)
    # Trung: width 35.0, height 21.6, under (Ký, họ tên) and above Đào Quang Trung
    rect_trung = fitz.Rect(407.5, 738.0, 442.5, 759.6)

    page.insert_image(rect_mem, stream=mem_png_bytes, keep_proportion=False)
    page.insert_image(rect_trung, stream=trung_png_bytes, keep_proportion=False)

    print("7. Saving final signed PDF...")
    doc.save(OUT_SIGNED, garbage=4, deflate=True)
    doc.close()

    shutil.copy2(OUT_SIGNED, OUT_MAIN)
    if os.path.exists(ARTIFACT_DIR):
        shutil.copy2(OUT_SIGNED, ARTIFACT_PDF)

    print("8. Generating verification preview renders...")
    doc_p = fitz.open(OUT_SIGNED)
    # Full page preview
    pix_full = doc_p[0].get_pixmap(dpi=150)
    pix_full.save(PREVIEW_FULL)

    # 300 DPI zoom render
    pix_300 = doc_p[0].get_pixmap(dpi=300)
    doc_p.close()

    h, w = pix_300.height, pix_300.width
    arr = np.frombuffer(pix_300.samples, dtype=np.uint8).reshape(h, w, 3)
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

    # Zoom of signature area (y=2875..3460, x=450..2200)
    zoom_sig = bgr[2875:3460, 450:2200]
    cv2.imwrite(PREVIEW_PNG, zoom_sig)

    # Zoom of Duy signature
    duy_zoom = bgr[3040:3190, 830:1210]
    cv2.imwrite(PREVIEW_DUY, duy_zoom)

    print("Done! PDF and previews generated successfully.")


if __name__ == '__main__':
    main()
