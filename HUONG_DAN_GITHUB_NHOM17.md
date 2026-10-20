# HƯỚNG DẪN CHIA SẺ CODE LÊN GITHUB CHUNG – NHÓM 17 (Selenium + Python + pytest)

Áp dụng cho kế hoạch Chương 4: 4 thành viên, mỗi người một module, TV1 giữ framework.

---

## 1. Thiết lập một lần (TV1 làm)

### 1.1. Tạo repo
- GitHub → **New repository** → tên: `coolmate-selenium-testing` → **Private** → tick *Add README* và *Add .gitignore: Python*.
- **Settings → Collaborators** → mời TV2, TV3, TV4 (quyền *Write*).

### 1.2. Bảo vệ nhánh `main`
**Settings → Branches → Add branch protection rule**, pattern `main`:
- [x] Require a pull request before merging
- [x] Require approvals: **1**
- [x] Dismiss stale approvals when new commits are pushed
- (Tùy chọn) Require status checks → khi đã có CI (mục 7)

→ Không ai push thẳng `main`; mọi thay đổi đi qua Pull Request (PR).

### 1.3. Cấu trúc thư mục chuẩn

```
coolmate-selenium-testing/
├── pages/                 # Page Object: mọi locator nằm ở đây
│   ├── base_page.py
│   ├── home_page.py
│   ├── login_page.py ...
├── tests/                 # chỉ gọi hành động nghiệp vụ, KHÔNG gọi By.* trực tiếp
│   ├── test_register.py
│   ├── test_login.py ...
├── utils/
│   ├── driver_factory.py
│   └── test_data.py
├── data/                  # CSV/JSON cho parametrize (KHÔNG chứa mật khẩu thật)
├── results/               # results.csv, report.html (chỉ commit bản chạy chính thức)
├── evidence/              # ảnh bằng chứng: <TC-ID>_<yyyymmdd>_<pass|fail>.png
├── docs/
│   ├── ch4/               # mỗi người một file .md: 4.2.3_search_filter.md ...
│   └── Test_case_Nhom17_Coolmate_Selenium.xlsx
├── .github/
│   └── pull_request_template.md
├── .env.example           # mẫu biến môi trường (KHÔNG có giá trị thật)
├── .gitignore
├── conftest.py            # fixture driver, hook chụp ảnh khi fail
├── pytest.ini
├── requirements.txt
└── README.md
```

### 1.4. Các file cấu hình cần có

**`.gitignore`** (bổ sung thêm vào bản Python mặc định):
```gitignore
# môi trường
.venv/
venv/
.env
# IDE
.idea/
.vscode/
# pytest / báo cáo tạm
.pytest_cache/
__pycache__/
*.pyc
allure-results/
# file tạm của Office
~$*
# ảnh/log chạy thử (chỉ commit bản chốt)
results/tmp/
evidence/tmp/
```

**`requirements.txt`** (ghim phiên bản để 4 máy giống nhau; điền đúng số bản của TV1 bằng `pip freeze`):
```text
selenium==<phiên bản>
pytest==<phiên bản>
pytest-html==<phiên bản>
webdriver-manager==<phiên bản>
python-dotenv==<phiên bản>
```

**`pytest.ini`**:
```ini
[pytest]
markers =
    smoke: chạy nhanh trước khi chạy full
    regression: bộ hồi quy
    high: test case ưu tiên cao
addopts = -v --html=results/report.html --self-contained-html
testpaths = tests
```

**`.env.example`** (mỗi người copy thành `.env` trên máy mình, `.env` đã bị ignore):
```text
BASE_URL=https://www.coolmate.me
TEST_EMAIL=
TEST_PASSWORD=
```

**`.github/pull_request_template.md`**:
```markdown
## Nội dung
- Module: (REG / LOG / SRC / ...)
- TC ID liên quan: (vd REG-01 → REG-05)

## Checklist
- [ ] Đã chạy `pytest -m smoke` và test của module, kết quả ổn định (≥ 3 lần liên tiếp)
- [ ] Locator chỉ nằm trong `pages/`, test không gọi `By.*`
- [ ] Không có `time.sleep` > 2 giây (dùng explicit wait)
- [ ] Tên hàm test = TC ID (vd `test_REG_01_register_valid`)
- [ ] Không commit mật khẩu, token, file `.env`
- [ ] Đã cập nhật cột Actual/Pass-Fail trong file test case (nếu có chạy)

## Ảnh/log (nếu có)
```

---

## 2. Mỗi thành viên cài đặt (một lần)

```bash
git clone https://github.com/<ten-org-hoac-user>/coolmate-selenium-testing.git
cd coolmate-selenium-testing

python -m venv .venv
# Windows:   .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # Windows (macOS/Linux: cp .env.example .env), rồi điền tài khoản test của bạn

git config user.name  "Ho Ten"
git config user.email "email-gan-voi-github@..."

pytest -m smoke             # kiểm tra chạy được
```

---

## 3. Quy trình làm việc hằng ngày (mô hình feature branch)

**Quy ước tên nhánh:** `feature/<module>` hoặc `feature/<module>-<việc>` — ví dụ `feature/register-login`, `feature/cart-voucher`, `fix/search-locator`, `docs/ch4-search`.

```bash
# 1) Luôn bắt đầu từ main mới nhất
git checkout main
git pull origin main

# 2) Tạo nhánh làm việc
git checkout -b feature/register-login

# 3) Code, chạy thử, rồi commit nhỏ và thường xuyên
git add pages/register_page.py tests/test_register.py
git commit -m "feat(register): add REG-01..REG-05 tests"

# 4) Trước khi push: cập nhật theo main để giảm xung đột
git fetch origin
git rebase origin/main        # hoặc: git merge origin/main (nếu chưa quen rebase)

# 5) Đẩy nhánh lên GitHub
git push -u origin feature/register-login
```

Sau đó vào GitHub → **Compare & pull request** → điền theo template → gán **reviewer** là buddy (TV1 ⇄ TV2, TV3 ⇄ TV4; riêng `ORD` thêm TV1) → chờ duyệt → **Squash and merge** → xóa nhánh.

### Quy ước commit
Dạng `<loại>(<module>): <mô tả ngắn>`

| Loại | Dùng khi |
|------|----------|
| `feat` | thêm test/page object mới |
| `fix` | sửa test/locator lỗi |
| `docs` | sửa báo cáo, README, test case |
| `refactor` | dọn code, không đổi hành vi |
| `chore` | cấu hình, requirements |
| `data` | cập nhật file dữ liệu `data/` |

---

## 4. Phân vùng file để tránh xung đột

Xung đột (conflict) xảy ra khi hai người sửa cùng một file. Cách tránh:

| Quy tắc | Chi tiết |
|---------|----------|
| Mỗi người một bộ file | TV2: `register_page.py`, `login_page.py`, `test_register.py`, `test_login.py`. TV3: `home/search/product`. TV4: `cart/checkout`. TV1: `account` + file khung |
| File khung chỉ TV1 sửa | `base_page.py`, `conftest.py`, `driver_factory.py`, `pytest.ini`, `requirements.txt`. Cần đổi → báo TV1 hoặc tạo PR riêng, TV1 duyệt |
| Báo cáo mỗi người một file | `docs/ch4/4.2.3_search_filter.md`… Không sửa file của người khác; TV1 ghép vào báo cáo chính |
| File test case Excel | Không dùng Git để merge `.xlsx`. Dùng **Google Sheets/OneDrive** làm bản làm việc chung; Git chỉ lưu bản chốt ở các Gate (1, 2, 3) |
| Commit nhỏ, pull thường xuyên | `git pull origin main` ít nhất mỗi đầu buổi |

### Nếu bị conflict
```bash
git fetch origin
git rebase origin/main
# Git báo conflict → mở file, tìm <<<<<<< ======= >>>>>>>, giữ đoạn đúng, xóa các dấu
git add <file-da-sua>
git rebase --continue
# (hoặc git rebase --abort để hủy và làm lại)
```

---

## 5. Quy tắc bảo mật (BẮT BUỘC)

- **Không commit**: mật khẩu, token, `.env`, cookie, thông tin cá nhân thật. Dùng `.env` + `python-dotenv`, chỉ commit `.env.example`.
- Nếu lỡ commit mật khẩu: **đổi mật khẩu ngay** (xóa commit chưa đủ vì lịch sử vẫn còn), rồi báo TV1.
- Repo để **Private**; chỉ chuyển Public khi giảng viên yêu cầu và đã rà soát sạch dữ liệu nhạy cảm.
- Dữ liệu test (`data/*.csv`) chỉ chứa dữ liệu giả hoặc email alias của nhóm.
- Ảnh bằng chứng: che thông tin cá nhân thật (SĐT, địa chỉ) nếu có.

---

## 6. Dùng GitHub cho công việc & lỗi (khớp kế hoạch)

- **GitHub Projects (Kanban):** cột `Backlog → Doing → Review → Done`; mỗi module hoặc nhóm TC là một card.
- **Issues cho lỗi:** tiêu đề `[BUG-xxx][MODULE] mô tả ngắn`.
  - Label: `severity:critical|major|minor` · `priority:high|medium|low` · `module:<tên>` · `status:open|confirmed|wontfix`.
  - Nội dung tối thiểu: TC ID, dữ liệu, bước tái hiện, kết quả mong đợi, kết quả thực tế, ảnh, trình duyệt + phiên bản, ngày giờ, người phát hiện.
- Tham chiếu trong commit/PR: `Closes #12` hoặc `Refs #12` để tự liên kết Issue.
- Chỉ tạo Issue **sau khi tái hiện bằng tay** (phân biệt lỗi thật của website với lỗi script/locator).

---

## 7. (Tùy chọn) Kiểm tra tự động bằng GitHub Actions

Chỉ chạy kiểm tra cú pháp/import, **không chạy test trên website thật bằng CI** (tránh spam đăng ký/đặt hàng, tránh bị chặn bot).

`.github/workflows/lint.yml`:
```yaml
name: lint
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt flake8
      - run: flake8 pages tests utils --max-line-length=120
      - run: pytest --collect-only -q   # chỉ kiểm tra test import/thu thập được, không chạy
```
Có thể bật job này làm *required status check* trong branch protection.

---

## 8. Mốc làm việc với Git theo Gate

| Thời điểm | Việc với Git |
|-----------|--------------|
| Ngày 1–2 | TV1 tạo repo, cấu hình mục 1, đẩy skeleton lên `main`; mời thành viên; mọi người clone + `pytest -m smoke` |
| Ngày 3 (Gate 1) | Tag `v0.1-testcases` khi đóng băng test case |
| Ngày 8 (Gate 2) | Mọi PR đã merge; tag `v0.2-scripts` |
| Ngày 10–11 | Chạy chính thức 1 lần; commit `results/` + `evidence/`; tag `v1.0-final-run` (Gate 3) |
| Ngày 12–13 | Chỉ sửa báo cáo, **không** sửa script/số liệu |

```bash
git tag -a v0.1-testcases -m "Dong bang test case (Gate 1)"
git push origin v0.1-testcases
```

---

## 9. Bảng lệnh Git thường dùng

| Mục đích | Lệnh |
|----------|------|
| Xem trạng thái | `git status` |
| Xem nhánh | `git branch -a` |
| Chuyển nhánh | `git checkout <nhánh>` |
| Lấy bản mới của main | `git checkout main && git pull origin main` |
| Hoàn tác file chưa commit | `git restore <file>` |
| Sửa message commit cuối (chưa push) | `git commit --amend` |
| Xem lịch sử gọn | `git log --oneline --graph -15` |
| Cất tạm thay đổi | `git stash` / `git stash pop` |

**Lỗi hay gặp:** (1) push thẳng `main` bị chặn → tạo nhánh rồi tạo PR; (2) quên `git pull` trước khi làm → conflict; (3) commit `.env` hoặc `.venv/` → kiểm tra `.gitignore`; (4) hai người sửa `conftest.py` → chỉ TV1 sửa.
