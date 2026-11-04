# DEBUG PDP-01: mã SP và SKU

Đã đọc ba file được yêu cầu, hai JSON và ảnh timeout trong `results/pdp_evidence/`.
URL Ultrawarm Puffer giữ nguyên, không thay cấu hình hoặc locator bằng phỏng đoán.

## Kết luận từ bằng chứng hiện có

- `open_url()` trước đây đòi `name`, `sku`, `price`; dừng ở `sku` trước assertion PDP-01.
- JSON `timeout_20261101_222937_982016.json`: `sku=[]`; `price`, `images`,
  `information`, `sizes` cũng không có match. Đây là bằng chứng locator chưa khớp,
  chưa đủ để kết luận website thiếu các trường này.
- Screenshot đang ở vùng gợi ý/đánh giá, thanh thông tin cố định cho thấy màu Đen V2,
  size L đã chọn. Không thấy mã trên vùng chụp; không suy rộng ra toàn trang.
- Không có DOM đầy đủ hoặc chuỗi bằng chứng trước/sau chọn biến thể. Chưa xác định
  được mã nằm ở đâu hoặc có chỉ xuất hiện sau lựa chọn hay không.
- Lần kiểm tra này: Python HTTPS bị `WinError 10013`; công cụ web cũng không truy cập
  được URL. Không tuyên bố đã kiểm chứng live DOM hoặc PASS UI.

## Thay đổi

`open_url()` kiểm tra URL/path và tên hiển thị, không đòi đủ mọi trường ngay khi mở.
PDP-01 chờ một lần cho snapshot UI, sau đó assertion báo tất cả trường thiếu/chưa đọc
được, vẫn yêu cầu tên, mã, giá, ảnh, mô tả, thông tin, size và size khả dụng.
Không có size khả dụng là FAILED. Snapshot các PDP khác giữ đường xử lý mặc định.
Không dùng `content`, JSON hoặc dữ liệu ẩn để điền mã trong PDP-01.
Diagnostic bổ sung body text và phần tử định danh (kèm trạng thái hiển thị); các dữ
liệu này chỉ để điều tra, không dùng làm dữ liệu assertion.

## Chạy trên Windows

Tại thư mục gốc, dùng URL `.env` hiện tại:

```powershell
python tools/run_pdp.py --collect-only -k PDP_01
python tools/run_pdp.py -k PDP_01 -x
Get-ChildItem results/pdp_evidence | Sort-Object LastWriteTime -Descending
```

Nếu FAIL, xem thông báo assertion và JSON mới (`reason`, `dom.visibleText`,
`dom.identifiers`, `matches`). Locator rỗng phải phân biệt với trường thực sự không
hiển thị; chưa sửa selector khi chưa xác minh DOM.

Mở cùng URL trong Chrome, về đầu trang. Trong DevTools Console chạy đoạn chỉ đọc
sau, lưu kết quả trước lựa chọn; sau đó click màu/size trên UI và chạy lại, chụp ảnh
vùng thông tin sản phẩm ở cả hai trạng thái:

```javascript
copy(JSON.stringify({
  url: location.href,
  text: document.body.innerText,
  identifiers: [...document.querySelectorAll(
    '[itemprop="sku"],[itemprop="productID"],[id*="sku" i],[class*="sku" i],'
    + '[id*="product-code" i],[class*="product-code" i]'
  )].map(e => ({html: e.outerHTML, text: e.innerText,
    rendered: !!e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden'}))
}, null, 2));
```

Đối với dòng mã tìm được qua body text, Inspect đúng phần tử để lấy CSS và xác nhận
nó thuộc sản phẩm chính, không thuộc gợi ý. Kiểm tra mã có thay đổi theo màu/size:
mã chung định danh sản phẩm, SKU biến thể định danh tổ hợp cụ thể. Việc mã không đổi
trong một lần thử chưa đủ chứng minh đó là mã chung; đối chiếu nhãn và đặc tả.
Không dùng SKU trong script/JSON/attribute ẩn làm bằng chứng mã hiển thị.

Nếu mã chỉ hiển thị sau lựa chọn, ghi rõ bước và so với Expected Result Bảng 4.11
trước khi sửa flow test. Hiện chưa có đủ Bảng 4.11 hoặc bằng chứng hành vi để tự thêm
bước chọn biến thể. Nếu xác nhận toàn UI không có mã SP theo yêu cầu, giữ FAILED
và ghi lỗi thiếu mã; không thay mã chung bằng SKU biến thể để PASS.

## Kiểm chứng đã thực hiện

- Compile trong bộ nhớ cả ba file Python: đạt.
- Collection: 16 test, chọn đúng 1 PDP-01, 15 deselected.
- Mô phỏng: trường thiếu được gom và gây AssertionError; metadata không thể điền mã.
- Đọc diff tại `docs/pdp01_sku_debug.diff`; bản trước sửa ở `docs/pdp01_sku_before.json`.
- Không chạy UI test do chặn mạng; không đổi kết quả CSV/HTML thành PASS.
- Không chỉnh REG, LOG, BasePage, ProductPage hoặc xóa hàm/class/test/file cũ.
