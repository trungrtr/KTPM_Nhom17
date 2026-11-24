import pymupdf
import cv2
import shutil
import os

pdf_orig = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4).pdf'

# Backup original once if not already backed up
backup_path = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_original.pdf'
if not os.path.exists(backup_path):
    shutil.copyfile(pdf_orig, backup_path)

doc = pymupdf.open(backup_path)
page = doc[0]

# High-res insertion paths
trung_png = 'tools/insert_trung.png'
mem_png = 'tools/insert_members.png'

# 1. Trung signature position (scaled to be nicely visible and centered):
# Center x = 425.0
# Width = 46.0 pt -> x0 = 402.0, x1 = 448.0
# y0 = 733.5, y1 = 766.0 (height = 32.5 pt)
rect_trung = pymupdf.Rect(402.0, 733.5, 448.0, 766.0)
page.insert_image(rect_trung, filename=trung_png, keep_proportion=True)

# 2. Members signatures position (scaled to be to và rõ, centered under Thành viên nhóm):
# Center x = 242.5
# Width = 92.0 pt -> x0 = 196.5, x1 = 288.5
# y0 = 736.5, y1 = 821.5 (height = 85.0 pt)
rect_mem = pymupdf.Rect(196.5, 736.5, 288.5, 821.5)
page.insert_image(rect_mem, filename=mem_png, keep_proportion=True)

# Save to both the original path and the _signed path
signed_path = r'docs/260903 - So tay mon hoc SoftwareTesting - IT6084.3 - Confirmation_sheet (4)_signed.pdf'
doc.save(signed_path)
doc.save(pdf_orig)
doc.close()

# Also copy to artifact dir for download
artifact_dir = r"C:\Users\daoqu\.gemini\antigravity\brain\86b168a6-89e3-416c-b5ed-b66361bda13a"
dest_pdf = os.path.join(artifact_dir, "Confirmation_sheet_Nhom17_signed.pdf")
shutil.copyfile(pdf_orig, dest_pdf)

# Render high-res 300 DPI preview for inspection
doc_final = pymupdf.open(pdf_orig)
page_final = doc_final[0]
pix = page_final.get_pixmap(dpi=300)
preview_path = os.path.join(artifact_dir, "preview_signed_confirmation_sheet.png")
pix.save(preview_path)
print(f"Saved signed PDF to:\n - {pdf_orig}\n - {signed_path}\n - {dest_pdf}")
print(f"Saved 300 DPI preview to: {preview_path} ({pix.width}x{pix.height})")
