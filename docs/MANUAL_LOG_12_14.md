# Kiểm thử thủ công LOG-12 và LOG-14

Hai test giữ nguyên thân hàm và được đánh dấu `@pytest.mark.skip(reason="Manual Testing")`.
Khi chạy pytest, HTML hiển thị SKIPPED với lý do Manual Testing; CSV LOG ghi
`Status=manual`: chờ người kiểm thử, không phải PASS/FAIL hay đã thực hiện.
Báo cáo các lần chạy cũ là lịch sử, không phản ánh phân loại mới này.

## Chuẩn bị

- Ghi ngày giờ, người thực hiện, URL, phiên bản triển khai, trình duyệt và phiên bản.
- Chuẩn bị tài khoản test hoạt động và email test chắc chắn chưa đăng ký.
- Dùng phiên trình duyệt sạch; chỉ dùng dữ liệu test, không ghi mật khẩu/token vào bằng chứng.
- CAPTCHA/OTP do người kiểm thử xử lý; nếu bị chặn, ghi trở ngại và để trống Pass/Fail.

## LOG-12 — Đăng xuất và Back

| Bước | Thao tác | Expected Result |
| --- | --- | --- |
| 1 | Mở trang đăng nhập, nhập tài khoản test hợp lệ, đăng nhập. | Đăng nhập thành công; truy cập được trang tài khoản được bảo vệ. |
| 2 | Đóng popup nếu có, ghi bằng chứng trước đăng xuất, chọn Đăng xuất. | Phiên đăng nhập kết thúc; không còn quyền truy cập tài khoản. |
| 3 | Nhấn Back trên trình duyệt, đợi trang tải xong. | Không khôi phục trạng thái đăng nhập hoặc quyền truy cập dữ liệu được bảo vệ. |
| 4 | Refresh rồi truy cập trực tiếp trang tài khoản (`/account` hoặc đường dẫn cấu hình). | Bắt buộc đăng nhập lại; hiển thị đầy đủ trường tài khoản, mật khẩu và nút đăng nhập. |

Actual Result (ghi theo từng bước):

Pass/Fail (chỉ điền sau khi thực hiện và đối chiếu đủ Expected Result):

Trở ngại / mã lỗi:

Bằng chứng (đường dẫn ảnh/video, bước tương ứng, thời điểm, URL đã ẩn dữ liệu nhạy cảm):

## LOG-14 — Quên mật khẩu

| Bước | Thao tác | Expected Result |
| --- | --- | --- |
| 1 | Mở trang đăng nhập trong phiên chưa đăng nhập, chọn Quên mật khẩu. | Hiển thị form khôi phục với trường email trống. |
| 2 | Để trống email, thử gửi yêu cầu; nếu nút bị vô hiệu hóa, ghi nhận và thử focus/blur. | Không gửi yêu cầu rỗng; có phản hồi bắt buộc nhập email. Chỉ nút bị vô hiệu hóa chưa đủ chứng minh phản hồi validation. |
| 3 | Mở lại form, nhập email tài khoản test đã đăng ký, gửi yêu cầu; xử lý CAPTCHA/OTP nếu có. | Có thông báo xác nhận khôi phục, không chỉ chuyển về trang đăng nhập mà không phản hồi; không tự đăng nhập tài khoản. |
| 4 | Mở lại form, nhập email test chưa đăng ký, gửi yêu cầu. | Có xác nhận chung để tránh dò tài khoản hoặc thông báo rõ email không tồn tại; không tự đăng nhập. |

Phạm vi đối chiếu test hiện tại là phản hồi giao diện, không khẳng định email đã được gửi tới hộp thư.

Actual Result (ghi theo từng bước):

Pass/Fail (chỉ điền sau khi thực hiện và đối chiếu đủ Expected Result):

Trở ngại / mã lỗi:

Bằng chứng (đường dẫn ảnh/video, bước tương ứng, thời điểm, thông báo hiển thị đã ẩn dữ liệu nhạy cảm):

## Chạy lại tự động

Chạy toàn bộ suite theo cấu hình dự án; LOG-12/14 được skip:

```powershell
python -m pytest -rs
```

CSV LOG: `results/log_test_results.csv`. HTML mặc định: `results/report.html`.
Các báo cáo này được tạo lại khi chạy suite; lưu báo cáo cũ nếu cần giữ lịch sử.
