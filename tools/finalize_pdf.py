import pymupdf
import cv2
import numpy as np
import shutil
import os

def generate_signed_pdf():
    # 1. Source reference PDF from which we extract the authentic sharp signatures
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

    # 2. Extract signatures with clean bounds (avoiding any printed headers/table lines)
    # Trung: signature only (between (Ký, họ tên) and Đào Quang Trung)
    crop_t = rubric[2050:2104, 1048:1140].copy()
    # Members: signatures and handwritten names only (under (Ký, họ tên))
    crop_m = rubric[2068:2275, 524:772].copy()

    # 3. Clean background to 100% pure white (255, 255, 255) preserving anti-aliased ballpoint strokes
    def clean_signature(crop, black=15, white=225, upscale=2):
        f = crop.astype(np.float32)
        levels = (f - black) / (white - black) * 255.0
        levels = np.clip(levels, 0, 255)
        levels[levels > 248] = 255
        res = levels.astype(np.uint8)
        
        # 2x Lanczos upscale for ultra-smooth rendering in PDF viewers
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

    # 4. Open original Confirmation Sheet
    pdf_orig = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
    doc = pymupdf.open(pdf_orig)
    page = doc[0]

    # Redact all 3 occurrences of '(Ký, họ tên)'
    rects = page.search_for('(Ký, họ tên)')
    for r in rects:
        r_exp = pymupdf.Rect(r.x0 - 2, r.y0 - 2, r.x1 + 2, r.y1 + 2)
        page.add_redact_annot(r_exp, fill=(1, 1, 1))
    page.apply_redactions()

    # 5. Insert Trung signature
    # Center x = 423.7, width = 50.0 pt -> x in [398.7, 448.7]
    # y in [730.0, 762.0] (height = 32.0 pt)
    rect_t = pymupdf.Rect(398.7, 730.0, 448.7, 762.0)
    page.insert_image(rect_t, filename=sig_t_path, keep_proportion=True)

    # 6. Insert Members signatures
    # Center x = 239.0, width = 96.0 pt -> x in [191.0, 287.0]
    # y in [730.0, 814.0] (height = 84.0 pt)
    rect_m = pymupdf.Rect(191.0, 730.0, 287.0, 814.0)
    page.insert_image(rect_m, filename=sig_m_path, keep_proportion=True)

    # 7. Save outputs
    target_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
    signed_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
    artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
    dest_pdf = os.path.join(artifact_dir, "Confirmation_sheet_Nhom17_signed.pdf")

    doc.save(target_pdf)
    doc.save(signed_pdf)
    doc.close()
    shutil.copyfile(target_pdf, dest_pdf)

    # 8. Render 300 DPI preview and zoom preview
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

    print("SUCCESS: Pure crisp signatures inserted into Confirmation Sheet.")
    print(f"Generated PDFs:\n  - {target_pdf}\n  - {signed_pdf}\n  - {dest_pdf}")
    print(f"Generated Previews:\n  - {preview_path}\n  - {zoom_path}")

if __name__ == '__main__':
    generate_signed_pdf()
