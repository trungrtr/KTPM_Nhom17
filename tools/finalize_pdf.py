import pymupdf
import cv2
import numpy as np
import shutil
import os

def generate_signed_pdf():
    # 1. Load source images
    ref_pdf = r'docs/Rubric_HopTacNhom_Nhom17_Signed (1).pdf'
    doc_ref = pymupdf.open(ref_pdf)
    page_ref = doc_ref[0]
    imgs = page_ref.get_images(full=True)
    if not imgs:
        raise RuntimeError("No image found in reference rubric PDF")
    
    xref = imgs[0][0]
    base_img = doc_ref.extract_image(xref)
    rubric_bytes = np.frombuffer(base_img["image"], dtype=np.uint8)
    rubric = cv2.imdecode(rubric_bytes, cv2.IMREAD_COLOR)
    doc_ref.close()

    # Load high-res photo for recovering any truncated strokes
    signed_photo_path = 'docs/signed.jpg'
    signed_photo = cv2.imread(signed_photo_path)
    if signed_photo is None:
        raise RuntimeError(f"Could not load {signed_photo_path}")

    # 2. Restore Duy's missing capital 'D' head
    # Clear region above y=2072 in rubric members column (x in [520, 775], y in [2020, 2072])
    rubric_restored = rubric.copy()
    rubric_restored[2020:2072, 520:775] = 255

    # Extract capital D head from signed_photo:
    # duy in signed_photo: y in [2120, 2265], x in [780, 1030]
    # D head: y in [2135, 2168], x in [782, 807] (33 x 25 px)
    d_head = signed_photo[2135:2168, 782:807].copy()
    b = d_head[:, :, 0].astype(float)
    r = d_head[:, :, 2].astype(float)

    # Clean alpha mask for blue ballpoint ink
    blue_diff = np.clip((b - r - 4.0) / 10.0, 0, 1)

    # Match rubric ballpoint pen color (navy blue B~100, G~85, R~85)
    d_clean = np.full_like(d_head, 255)
    for c in range(3):
        ink_c = np.clip(d_head[:, :, c].astype(float) * 0.70, 0, 255)
        d_clean[:, :, c] = (255.0 * (1 - blue_diff) + ink_c * blue_diff).astype(np.uint8)

    # Attach restored D head seamlessly onto rubric at x in [575, 600], y in [2039, 2072]
    rubric_restored[2039:2072, 575:600] = np.minimum(rubric_restored[2039:2072, 575:600], d_clean)

    # 3. Extract crops
    # Members (with full capital D restored): y in [2036, 2275], x in [520, 775]
    crop_m = rubric_restored[2036:2275, 520:775].copy()
    # Trung: y in [2050, 2104], x in [1048, 1140]
    crop_t = rubric_restored[2050:2104, 1048:1140].copy()

    # 4. Clean background to 100% vector pure white (255, 255, 255) and upscale 2x Lanczos
    def clean_signature(crop, black=15, white=225, upscale=2):
        f = crop.astype(np.float32)
        levels = (f - black) / (white - black) * 255.0
        levels = np.clip(levels, 0, 255)
        levels[levels > 248] = 255
        res = levels.astype(np.uint8)
        if upscale > 1:
            res = cv2.resize(res, (res.shape[1] * upscale, res.shape[0] * upscale), interpolation=cv2.INTER_LANCZOS4)
            res[res > 248] = 255
        return res

    sig_t = clean_signature(crop_t, black=15, white=225, upscale=2)
    sig_m = clean_signature(crop_m, black=10, white=225, upscale=2)

    os.makedirs('tools/output', exist_ok=True)
    sig_t_path = 'tools/output/final_sig_trung.png'
    sig_m_path = 'tools/output/final_sig_mem.png'
    cv2.imwrite(sig_t_path, sig_t)
    cv2.imwrite(sig_m_path, sig_m)

    # 5. Open original Confirmation Sheet
    pdf_orig = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
    doc = pymupdf.open(pdf_orig)
    page = doc[0]

    # Redact all 3 occurrences of '(Ký, họ tên)'
    rects = page.search_for('(Ký, họ tên)')
    for r in rects:
        r_exp = pymupdf.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        page.add_redact_annot(r_exp, fill=(1, 1, 1))
    page.apply_redactions()

    # 6. Insert Trung signature
    # Center x = 423.7, width = 50.0 pt -> x in [398.7, 448.7]
    # y in [730.0, 762.0] (height = 32.0 pt)
    rect_t = pymupdf.Rect(398.7, 730.0, 448.7, 762.0)
    page.insert_image(rect_t, filename=sig_t_path, keep_proportion=True)

    # 7. Insert Members signatures (with full Duy capital D, Quân, Lâm)
    # Center x = 239.0, width = 96.0 pt -> x in [191.0, 287.0]
    # y in [728.0, 818.0] (height = 90.0 pt)
    rect_m = pymupdf.Rect(191.0, 728.0, 287.0, 818.0)
    page.insert_image(rect_m, filename=sig_m_path, keep_proportion=True)

    # 8. Save outputs
    target_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
    signed_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
    artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
    dest_pdf = os.path.join(artifact_dir, "Confirmation_sheet_Nhom17_signed.pdf")

    doc.save(target_pdf)
    doc.save(signed_pdf)
    doc.close()
    shutil.copyfile(target_pdf, dest_pdf)

    # 9. Render 300 DPI preview and zoom preview
    doc_out = pymupdf.open(target_pdf)
    page_out = doc_out[0]
    pix = page_out.get_pixmap(dpi=300)
    preview_path = os.path.join(artifact_dir, "preview_signed_confirmation_sheet.png")
    pix.save(preview_path)
    doc_out.close()

    preview_bgr = cv2.imread(preview_path)
    h, w, c = preview_bgr.shape
    sig_zoom = preview_bgr[int(705 * 300 / 72):int(825 * 300 / 72), int(160 * 300 / 72):int(480 * 300 / 72)]
    zoom_path = os.path.join(artifact_dir, "preview_signature_zoom.png")
    cv2.imwrite(zoom_path, sig_zoom)

    print("SUCCESS: Fully restored signatures inserted into Confirmation Sheet.")
    print(f"Generated PDFs:\n  - {target_pdf}\n  - {signed_pdf}\n  - {dest_pdf}")
    print(f"Generated Previews:\n  - {preview_path}\n  - {zoom_path}")

if __name__ == '__main__':
    generate_signed_pdf()
