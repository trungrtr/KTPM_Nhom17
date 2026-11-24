import pymupdf
import cv2
import numpy as np
import shutil
import os

pdf_orig = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
doc = pymupdf.open(pdf_orig)
page = doc[0]

# 1. Redact / remove all '(Ký, họ tên)' occurrences
rects = page.search_for('(Ký, họ tên)')
print(f"Redacting {len(rects)} occurrences of (Ký, họ tên)...")
for r in rects:
    # Slightly expand redaction box by 0.5pt to ensure no text edge artifacts remain
    r_exp = pymupdf.Rect(r.x0 - 1, r.y0 - 1, r.x1 + 1, r.y1 + 1)
    page.add_redact_annot(r_exp, fill=(1, 1, 1))

page.apply_redactions()

# 2. Prepare cropped HD signatures
trung_hd = cv2.imread('tools/trung_hd.png', cv2.IMREAD_UNCHANGED)
mem_hd = cv2.imread('tools/members_hd.png', cv2.IMREAD_UNCHANGED)

# Crop to tight bounding box with 6px padding
a_t = trung_hd[:, :, 3]
yt, xt = np.where(a_t > 20)
trung_tight = trung_hd[max(0, np.min(yt)-6):min(trung_hd.shape[0], np.max(yt)+7),
                       max(0, np.min(xt)-6):min(trung_hd.shape[1], np.max(xt)+7)]

a_m = mem_hd[:, :, 3]
ym, xm = np.where(a_m > 20)
mem_tight = mem_hd[max(0, np.min(ym)-6):min(mem_hd.shape[0], np.max(ym)+7),
                   max(0, np.min(xm)-6):min(mem_hd.shape[1], np.max(xm)+7)]

cv2.imwrite('tools/trung_tight_hd.png', trung_tight)
cv2.imwrite('tools/members_tight_hd.png', mem_tight)
print(f"trung_tight_hd: {trung_tight.shape}, members_tight_hd: {mem_tight.shape}")

# 3. Insert Trung signature
# Box: y in [725.0, 764.5], centered at x = 425.0, width = 48.0 pt
rect_trung = pymupdf.Rect(401.0, 725.0, 449.0, 764.5)
page.insert_image(rect_trung, filename='tools/trung_tight_hd.png', keep_proportion=True)

# 4. Insert Members signatures
# Box: y in [726.0, 818.0], centered at x = 242.5, width = 96.0 pt
rect_mem = pymupdf.Rect(194.5, 726.0, 290.5, 818.0)
page.insert_image(rect_mem, filename='tools/members_tight_hd.png', keep_proportion=True)

# 5. Save output PDFs
target_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'
signed_pdf = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
dest_pdf = os.path.join(artifact_dir, "Confirmation_sheet_Nhom17_signed.pdf")

doc.save(target_pdf)
doc.save(signed_pdf)
doc.close()
shutil.copyfile(target_pdf, dest_pdf)

# 6. Render high-res 300 DPI preview
doc_out = pymupdf.open(target_pdf)
page_out = doc_out[0]
pix = page_out.get_pixmap(dpi=300)
preview_path = os.path.join(artifact_dir, "preview_signed_confirmation_sheet.png")
pix.save(preview_path)

# Also render close-up zoom at 300 DPI
preview_bgr = cv2.imread(preview_path)
h, w, c = preview_bgr.shape
sig_zoom = preview_bgr[int(h * 0.82):int(h * 0.98), int(w * 0.15):int(w * 0.90)]
zoom_path = os.path.join(artifact_dir, "preview_signature_zoom.png")
cv2.imwrite(zoom_path, sig_zoom)

print("SUCCESS: PDF updated, 300 DPI preview and zoom generated!")
