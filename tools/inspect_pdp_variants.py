"""Interactive evidence collection; never creates or approves a test oracle."""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils import config  # noqa: E402,F401
from utils.driver_factory import create_driver  # noqa: E402
from pages.product_page import ProductPage  # noqa: E402


def main():
    driver = create_driver()
    folder = ROOT / "results" / "pdp_evidence"
    folder.mkdir(parents=True, exist_ok=True)
    try:
        page = ProductPage(driver).open_url(os.environ["PDP_URL_IN_STOCK"])
        print("Chon tung mau bang tay, doi gallery tai xong va kiem tra anh/gia/size.")
        print("Enter: luu bang chung; q: ket thuc. Khong tu tao oracle.")
        while input("> ").strip().lower() != "q":
            stamp = datetime.now().strftime("manual_%Y%m%d_%H%M%S_%f")
            gallery = page.pdp02_gallery_state()
            data = {"captured_at": datetime.now().isoformat(),
                    "colors": page.variant_evidence("colors"),
                    "sizes": page.variant_evidence("sizes"),
                    "price": page.price(),
                    "images": page.image_sources(pdp02_gallery=gallery),
                    "gallery_state": gallery,
                    "image_contract": "gallery-clipped-loaded-currentSrc-exact-v1",
                    "image_dom": page.pdp02_image_debug(),
                    "variants_html": driver.find_element("id", "product-detail-variants").get_attribute("outerHTML")}
            path = folder / (stamp + ".json")
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            driver.save_screenshot(str(folder / (stamp + ".png")))
            print(path)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
