# PDP-04/05/06/09 — kết quả hoàn thiện

## Kết quả kiểm chứng

Chỉ sửa `pages/pdp_support.py`, các thân test PDP-04/05/06/09 trong
`tests/test_chi_tiet_san_pham.py`, và thêm tùy chọn thư mục báo cáo
`PDP_REPORT_DIR` trong plugin báo cáo PDP. Không xóa file/hàm/class/test/dữ liệu.
Không sửa REG/LOG, fixture dùng chung, dữ liệu CSV hoặc oracle PDP-02.

| Case | Pytest thực chạy | Báo cáo tổng hợp |
|---|---|---|
| PDP-04 | SKIPPED | SKIP: thiếu bộ dữ liệu hết hàng đã xác minh |
| PDP-05 | FAILED | FAIL môi trường: Chrome tab crashed khi mở URL; chưa xác minh nghiệp vụ |
| PDP-06: 1, 2, 5, 0, -1, 99999, abc | 7 FAILED | FAIL môi trường: Chrome tab crashed khi mở URL; chưa xác minh nghiệp vụ |
| PDP-07 | SKIPPED | PASS (Manual), theo xác nhận của người dùng |
| PDP-08 | SKIPPED | PASS (Manual), theo xác nhận của người dùng |
| PDP-09 | FAILED | FAIL môi trường: Chrome tab crashed khi mở URL; chưa xác minh nghiệp vụ |
| PDP-10 | SKIPPED | PASS (Manual), theo xác nhận của người dùng |

Tổng phiên chọn lọc: **9 failed, 4 skipped, 3 deselected**, 31.74 giây theo
Pytest. PDP-01/02/03 không được chạy. Không có PASS automation được tuyên bố.
Không có thời điểm thực hiện hoặc thời lượng manual được cung cấp; không suy
diễn từ thời gian Pytest bỏ qua test. Decorator/lý do skip cũ của 07/08/10 được
giữ nguyên theo yêu cầu không sửa kịch bản; xác nhận manual tại bảng này thay
thế nhận định “chưa thực hiện” trong nội dung lịch sử đó.

Log: `results/pdp_04050609_review/live.log`. CSV/HTML Pytest nằm tại
`results/pdp_04050609_review/automation/`. Lần đầu launcher kiểm tra bị lỗi
fixture self đã được sửa; log lỗi ban đầu giữ riêng ở
`launcher_initial_error.log`, không dùng làm kết quả kiểm chứng UI.

## Thay đổi và giới hạn

- PDP-04: kiểm tra đủ URL/size/màu trước khi mở browser; xác nhận size disabled,
  native pointer click không thay đổi lựa chọn và size hết hàng không selected.
  Size còn hàng mặc định không làm test bị SKIP sau khi đã xác minh size hết
  hàng không thể chọn. Không bấm Add cho size còn hàng để giả lập mua size hết
  hàng. Phạm vi tự động hiện tại là chặn chọn size hết hàng trong màu cấu hình;
  màu bị disabled toàn bộ cần kiểm tra manual riêng.
- PDP-05: thử click Selenium vào lựa chọn đang selected và đợi trạng thái ổn
  định. Nếu không thể bỏ chọn bằng UI, SKIP với lý do N/A. Nếu tạo được thiếu
  thuộc tính, giữ kiểm tra Add bị chặn hoặc thông báo yêu cầu chọn và kiểm tra
  giỏ sau reload không đổi. Không chỉnh state bằng JavaScript.
- PDP-06: DOM lưu có input text `#quantity-input`, nút tăng/giảm sibling với
  aria-label tiếng Việt. Helper mới giới hạn số click, kiểm tra 1 → 2 → 5 → 2 → 1,
  đọc trạng thái disabled của nút giảm và kiểm tra min=1 cả khi nút vẫn enabled.
  Với 0/-1/abc chỉ nhập nếu input editable. Nếu chỉ có counter/nút, SKIP N/A và
  chuyển kiểm tra biên sang manual. Với 99999 chỉ kiểm tra nếu input editable
  và có max công bố; không có max thì SKIP, không đoán giới hạn. Không click
  hàng chục nghìn lần. DOM lịch sử không chứng minh UI hiện tại đã PASS.
- PDP-09: locator được đối chiếu với DOM đã lưu ở
  `results/pdp_evidence/pdp02_cookie_popup.html`: section aria-label “Gợi ý sản
  phẩm”, link có ga-tracking-value `product-detail__product-suggestion`, tên
  trong aria-label `View details for ...`. Cuộn section, đợi link, click native,
  hỗ trợ tab mới, so sánh đường dẫn URL và tên h1 đích. Không dùng toàn bộ nội
  dung card (giá, size) làm tên. Không có link hợp lệ thì SKIP với lý do hiện có;
  phải kiểm tra DOM thủ công để phân biệt thiếu gợi ý và locator thay đổi.

Cookie/overlay sử dụng helper PDP hiện có. JavaScript bổ sung chỉ cuộn trang,
không ép click, bỏ disabled hoặc gán giá trị. Chờ bằng WebDriverWait.

## Dữ liệu .env còn thiếu

Ba biến sau hiện trống/chưa khai báo; phải lấy từ cùng một tổ hợp thực tế:

```dotenv
PDP_URL_SOLDOUT=https://www.coolmate.me/product/<slug>?color=<color-slug>
PDP_SOLDOUT_SIZE=<nhãn size hiển thị>
PDP_SOLDOUT_COLOR=<nhãn màu hiển thị>
```

Không dùng URL mẫu này làm dữ liệu thật. `PDP_URL_IN_STOCK` và
`PDP_VARIANT_EXPECTATIONS` đã có; không thiếu biến bắt buộc khác cho 05/06/09.

Cách xác minh: mở PDP trong trình duyệt mới, chấp nhận cookie, chọn màu còn có
thể truy cập, tìm size được đánh dấu hết hàng. Dùng DevTools kiểm tra button
size có disabled/aria-disabled hoặc trạng thái hết hàng; kiểm tra bằng click
người dùng rằng không chọn được size đó. Ghi URL sau chọn màu, nhãn màu, nhãn
size chính xác, ảnh chụp và thời điểm xác minh. Reload xác nhận lại trước khi
điền .env vì tồn kho có thể thay đổi. Sản phẩm hiện cấu hình chưa được xác minh
có size hết hàng; không tự gán một sản phẩm/tổ hợp làm dữ liệu đã kiểm chứng.

## Kiểm tra bảo toàn

- Compile 78 file Python: PASS.
- Collection: 16 test, PASS.
- AST: giữ toàn bộ tên hàm/class; các test ngoài phạm vi và decorator manual
  không thay đổi.
- Hash các file nguồn/dữ liệu/báo cáo cũ được ghi trong baseline; REG/LOG và
  báo cáo cũ không thay đổi. Cache Python phát sinh không phải source.
- Thư mục không có Git repository; unified diff:
  `results/pdp_04050609_review/changes.diff`, baseline và verification JSON
  cùng thư mục. Code mới vẫn cần xác minh UI sau khi xử lý Chrome crash.

## Chạy lại từ thư mục project bằng PowerShell

```powershell
$env:PDP_REPORT_DIR = Join-Path (Get-Location) ('results/pdp_rerun_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
python tools/run_pdp.py --collect-only
python tools/run_pdp.py -k 'PDP_04 or PDP_05 or PDP_06 or PDP_07 or PDP_08 or PDP_09 or PDP_10'
```

Runner bình thường tái sử dụng fixture hiện có. Để tái hiện phiên chẩn đoán
với ChromeDriver đã cache trong workspace, không tải driver mới:

```powershell
$env:HEADLESS = 'true'
python results/pdp_04050609_review/run_live.py
python results/pdp_04050609_review/verify.py
```

Launcher chẩn đoán ghi đè **chỉ** báo cáo trong thư mục automation riêng nêu
trên. Nếu cần giữ phiên đó, dùng runner bình thường với thư mục có timestamp.
