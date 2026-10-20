# coolmate-selenium-testing (Nhóm 17)
Kiểm thử website Coolmate bằng Selenium + Python + pytest, theo mô hình Page Object Model (POM).

## Chạy thử trong 5 phút
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
pytest -m smoke
```
Báo cáo HTML: `results/report.html` · Kết quả từng TC: `results/results.csv` · Ảnh lỗi: `evidence/auto/`.

## Cấu trúc
- `pages/` Page Object (locator + hành động nghiệp vụ) · `pages/components/` thành phần dùng chung
- `tests/` test case (tên hàm = TC ID) · `utils/` driver, cấu hình, đọc dữ liệu
- `data/` CSV cho parametrize · `evidence/` ảnh bằng chứng · `docs/ch4/` bản thảo báo cáo
