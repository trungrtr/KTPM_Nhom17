import pymupdf
import cv2
import shutil
import os

pdf_orig = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
doc = pymupdf.open(pdf_orig)
page = doc[0]

# 1. Redact all 3 occurrences of '(Ký, họ tên)'
rects = page.search_for('(Ký, họ tên)')
print(f"Redacting {len(rects)} occurrences of (Ký, họ tên)...")
for r in rects:
    r_exp = pymupdf.Rect(r.x0 - 1.5, r.y0 - 1.5, r.x1 + 1.5, r.y1 + 1.5)
    page.add_redact_annot(r_exp, fill=(1, 1, 1))

page.apply_redactions()

# 2. Insert pure crisp Trung signature (NO (Ký, họ tên))
# Rect: centered at x=425.0, width=52.5 pt -> x in [398.75, 451.25]
# y in [731.0, 761.0], height=30.0 pt
rect_trung = pymupdf.Rect(398.75, 731.0, 451.25, 761.0)
page.insert_image(rect_trung, filename='tools/trung_pure_crisp.png', keep_proportion=True)

# 3. Insert pure crisp Members signatures (NO (Ký, họ tên))
# Rect: centered at x=242.5, width=96.2 pt -> x in [194.4, 290.6]
# y in [730.0, 812.0], height=82.0 pt
rect_mem = pymupdf.Rect(194.4, 730.0, 290.6, 812.0)
page.insert_image(rect_mem, filename='tools/mem_pure_crisp_padded.png', keep_proportion=True)

# 4. Save output PDFs
target_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
signed_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
dest_pdf = os.path.join(artifact_dir, "Confirmation_sheet_Nhom17_signed.pdf")

doc.save(target_pdf)
doc.save(signed_pdf)
doc.close()
shutil.copyfile(target_pdf, dest_pdf)

# 5. Render 300 DPI preview and zoom
doc_out = pymupdf.open(target_pdf)
page_out = doc_out[0]
pix = page_out.get_pixmap(dpi=300)
preview_path = os.path.join(artifact_dir, "preview_signed_confirmation_sheet.png")
pix.save(preview_path)

# Close up zoom at 300 DPI
preview_bgr = cv2.imread(preview_path)
h, w, c = preview_bgr.shape
sig_zoom = preview_bgr[int(h * 0.83):int(h * 0.98), int(w * 0.15):int(w * 0.90)]
zoom_path = os.path.join(artifact_dir, "preview_signature_zoom.png")
cv2.imwrite(zoom_path, sig_zoom)

print("SUCCESS: Pure crisp signatures inserted into PDF, 300 DPI preview and zoom generated!")
