# Sửa kiểm thử LOG sau đánh giá 31/10/2026

## Phạm vi và bằng chứng

Chỉ sửa `pages/login_page.py`, `tests/test_dang_nhap.py` và phần LOG trong `tests/conftest.py`. Giữ nguyên thân test LOG-01, toàn bộ phần hook REG, BasePage, RegisterPage, driver factory và root conftest. Không bỏ hàm/class/test hiện có. Bản trước sửa và diff nằm tại `results/log_qa_fix/`.

LOG-02/09-email/12/13: JSON mới ghi nhận trang chủ, generic error và không có auth controls. Không đủ bằng chứng xác định website từ chối thông tin; helper trước đây kết luận rejection từ generic error quá sớm. Helper mới đợi auth/challenge/lỗi credential được nhận diện trên form; lưu evidence trước khi probe account độc lập. Dù có redirect hoặc link account, vẫn phải có tín hiệu authenticated tại trang được bảo vệ. Không retry đăng nhập và không tự chuẩn hóa SĐT để che vấn đề dữ liệu.

LOG-09 giữ hai test độc lập có assertion riêng; nhánh password kiểm chứng login đúng, logout rồi mới thử swapcase. Nếu baseline không dùng được, ca không được PASS chỉ nhờ mọi mật khẩu đều bị từ chối. LOG-12 giữ history để kiểm tra Back, refresh và truy cập account; LOG-13 nhận diện challenge sau reload/tab. Các ca này dùng helper account mới và xử lý popup hiện hữu. Chưa khẳng định đã xử lý mọi biến thể COOL CLUB ngoài thực tế.

LOG-05/06/07 dùng `validity.valueMissing` hoặc required message gắn đúng trường; không đợi server khi đã đủ chứng cứ client. Nút disabled thiếu phản hồi bắt buộc vẫn FAIL, không tự tính PASS. LOG-08 đòi bằng chứng format đúng identity, có challenge guard khi load lại. LOG-11 giữ nguyên test, sửa clickable chỉ trong LoginPage để chọn bản control đang hiện và enabled. LOG-14 chờ form password biến mất trước khi tìm reset email, chặn CAPTCHA và không chấp nhận error tùy ý cho email lạ. Selector reset/COOL CLUB vẫn cần kiểm chứng live, chưa có bằng chứng để tự đổi sang selector mới.

Lỗi driver/network không còn được tự chuyển thành SKIP do giới hạn môi trường. Thiếu dữ liệu và challenge vẫn được ghi SKIP theo tiền điều kiện hiện hữu, không bypass. Mật khẩu sai được tạo cùng độ dài và nhóm ký tự đầu để giảm khả năng kiểm tra nhầm maxlength. Không chạy LOG-10 hoặc gửi email reset trong đợt này.

Hook LOG giữ browser trên test node để không mất khi fixture được gọi động/teardown; CSV có thêm Node_ID/Run_ID/Phases, tổng hợp setup/call/teardown. CSV chính chỉ chứa phiên mới, phiên cũ được copy vào `results/log_runs/<run_id>/previous_log_test_results.csv` trước khi ghi lại. Diagnostic lỗi lưu theo run thay vì ghi đè. Không thay phần reset/ghi CSV REG. Chưa hỗ trợ chạy nhiều worker; chạy tuần tự.

## Xác minh đã thực hiện

- Compile/AST cả ba file, xác nhận không mất định nghĩa, thân LOG-01 không đổi và phần REG của conftest không đổi.
- Kiểm tra offline bằng `python results/log_qa_fix/check_offline.py`: generic alert ngoài login không thành credential rejection; phân biệt challenge/client-validation/rejection/unresolved; kiểm tra account độc lập khi chưa xác định; lỗi credential không thành PASS; native required không dùng server wait; clickable chọn bản đang hiện; dữ liệu sai giữ độ dài; CSV mới có browser/nodeid và bảo toàn phiên trước cùng REG CSV giả lập.
- Không chạy pytest của dự án để tránh các hook làm thay đổi báo cáo hiện có. Script offline dùng AST và thư mục tạm, không import config hay đọc `.env`.
- GET chỉ đọc `https://www.coolmate.me/login` bằng urllib gặp `URLError` trong môi trường Codex. Không có kết quả Selenium live mới. Các kiểm tra offline không thay thế E2E và không chứng minh LOG-01 tiếp tục PASS khi dùng helper chung đã thay đổi.

## Lệnh chạy lại trong PowerShell Windows

Chạy từ thư mục gốc dự án, dùng môi trường đã cài requirements. Tài khoản, SĐT liên kết và email chưa đăng ký phải được người quản lý dữ liệu xác nhận. Không in giá trị mật khẩu. Những lệnh sau không chọn REG hoặc LOG-10. HTML dùng tên riêng tránh ghi đè báo cáo cũ; mỗi lệnh tạo phiên CSV LOG mới và lưu phiên CSV trước.

Nhóm kiểm tra client và locator trước:

```powershell
$logRun = Get-Date -Format 'yyyyMMdd_HHmmss'
python -m pytest tests/test_dang_nhap.py -o addopts= -p no:cacheprovider -k 'LOG_05 or LOG_06 or LOG_07 or LOG_11' --html="results/log_client_$logRun.html" --self-contained-html --tb=short -rs
```

Sau đó baseline LOG-01 và các ca đăng nhập/session cần sửa. Lệnh này có các lần nhập sai của LOG-03/04/08/09; chỉ chạy một lượt tuần tự, không thêm rerun/xdist, dừng nếu hệ thống bảo vệ tài khoản kích hoạt:

```powershell
$logRun = Get-Date -Format 'yyyyMMdd_HHmmss'
python -m pytest tests/test_dang_nhap.py -o addopts= -p no:cacheprovider -k 'not LOG_10 and not LOG_14' --html="results/log_verify_$logRun.html" --self-contained-html --tb=short -rs -x
```

`-x` dừng ngay lỗi đầu để khảo sát trước khi tiếp tục; CSV lúc đó chỉ chứa các test đã thực hiện. Để chẩn đoán riêng SĐT sau khi baseline đã đạt:

```powershell
$logRun = Get-Date -Format 'yyyyMMdd_HHmmss'
python -m pytest tests/test_dang_nhap.py::test_LOG_02_phone -o addopts= -p no:cacheprovider --html="results/log_phone_$logRun.html" --self-contained-html --tb=short -rs
```

Chỉ chạy LOG-14 một lần khi đã được phép gửi yêu cầu tới hai email test được kiểm soát:

```powershell
$logRun = Get-Date -Format 'yyyyMMdd_HHmmss'
python -m pytest tests/test_dang_nhap.py::test_LOG_14_forgot_password -o addopts= -p no:cacheprovider --html="results/log_reset_$logRun.html" --self-contained-html --tb=short -rs
```

Không cung cấp lệnh full suite mặc định bao gồm LOG-10: cần account riêng và chính sách bảo vệ được xác nhận trước. CAPTCHA/OTP phải được ghi nhận đúng là chặn tự động, không PASS validation.

## Phần còn cần xác nhận

Chưa kết luận website từ chối SĐT hay UI/auth locator chưa khớp; cần kết quả helper mới và diagnostic cùng run. Chưa xác minh selector COOL CLUB/reset/toggle trên DOM hiện tại, native/ARIA required thực tế, chính sách email case/trim, session và chống dò account. Không tự thêm selector phỏng đoán hoặc hạ assertion để đạt PASS. Các ca LOG-08/14 vẫn giữ nhóm trường hợp trong hàm cũ để hạn chế thay đổi; tách từng dữ liệu tiếp nếu traceback live cho thấy cần phân lập coverage. Root hook/CSV chung giữ nguyên để không tác động REG; nó vẫn có hành vi xóa `results/results.csv` khi bắt đầu pytest và ảnh FAIL chưa che dữ liệu. Không công bố ảnh có thông tin nhạy cảm.
