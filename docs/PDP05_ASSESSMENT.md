# Đánh giá PDP-05 — Thêm vào giỏ khi thiếu thuộc tính

Ngày đánh giá: 04/11/2026. Kết luận: **N/A — giữ SKIPPED**, không tính PASS.

## Phạm vi và bằng chứng

Sản phẩm đang cấu hình: Áo phao dày Ultrawarm Puffer có mũ II, URL có `?color=den-v2`. Kết luận chỉ áp dụng cho sản phẩm và luồng này; không khẳng định mọi sản phẩm Coolmate đều tự chọn thuộc tính.

- [DOM và trạng thái trước/sau](../results/pdp0205_fix/pdp05_1793729478209460100.json).
- [HTML sau thao tác](../results/pdp0205_fix/pdp05_1793729478209460100.html).
- [Screenshot sau thao tác](../results/pdp0205_fix/pdp05_1793729478209460100.png).

Trước thao tác, màu **Đen V2** và size **M** đã được chọn. Size là `button` với token class `bg-neutral-900 text-light`; màu là liên kết `a` trỏ tới URL màu hiện tại. Screenshot xác nhận nhãn “Màu sắc: Đen V2”, “Kích thước: M” và trạng thái chọn tương ứng. Do URL đã chỉ định màu, bằng chứng này không chứng minh màu mặc định khi mở URL không có query.

## Thao tác UI đã được ghi nhận

Luồng Selenium hiện hành xử lý Cookie/overlay, cuộn tới size đang chọn, click native vào M, chờ trạng thái ổn định; sau đó click native vào liên kết màu đang chọn và chờ ổn định. Không dùng JavaScript thay đổi state. Bằng chứng lần chạy lưu kết quả `Skipped: N/A: native clicks on selected options retain complete color/size; no UI deselection`.

Sau các thao tác, lựa chọn vẫn là **Đen V2 / M**. Các option đều hiển thị và khả dụng; không có bằng chứng lỗi locator/click trong lần chạy này. DOM khu vực thuộc tính không có control xóa lựa chọn. Với các control hiện có, chưa tạo được trạng thái thiếu màu hoặc size bằng thao tác UI hợp lệ.

## Kết luận cho báo cáo

**PDP-05: SKIPPED, phân loại N/A do không đạt tiền điều kiện tạo trạng thái thiếu thuộc tính qua UI của sản phẩm kiểm thử.** Chưa thực hiện bước “Thêm vào giỏ khi thiếu thuộc tính”, vì vậy chưa xác minh được cơ chế từ chối thêm hoặc assertion giỏ không thay đổi trong trạng thái đó. Không đánh PASS và không kết luận website có lỗi chức năng.

Giữ nguyên test và các assertion hiện có: nếu sau này UI cho phép bỏ chọn, test sẽ tiếp tục kiểm tra phản hồi khi thêm và giỏ không thay đổi. Không cần sửa automation theo bằng chứng hiện có.

## Giới hạn lần đánh giá lại

Đã thử chạy riêng PDP-05 lần nữa, báo cáo tách biệt tại `results/pdp05_reassessment/`. Lần chạy này dừng trước khi mở website bởi `PermissionError` khi `webdriver_manager` gọi `os.chmod` lên ChromeDriver trong cache ngoài workspace. Đây là lỗi môi trường của lần chạy mới, không chuyển thành N/A và không thay thế bằng chứng SKIPPED trước đó. Chưa có xác nhận UI live mới trong phiên đánh giá này.

Chỉ thêm tài liệu đánh giá này; không sửa test, helper, dữ liệu, kết quả cũ, REG/LOG hay các PDP khác.
