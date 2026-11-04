# PDP — Bảng 4.11

## Debug PDP-02/03 (2026-11-03)

`.env` nhận **đường dẫn file JSON**, không nhận JSON trực tiếp:

```dotenv
PDP_VARIANT_EXPECTATIONS=data/pdp_variant_expectations.json
```

Đường dẫn tương đối được tính từ thư mục chạy lệnh (gốc project). File UTF-8 không BOM,
JSON chuẩn: dấu nháy kép, boolean `true`/`false`, không comment hay dấu phẩy cuối.
Chỉ thêm dòng trên sau khi đã tạo và duyệt file dữ liệu thật theo cấu trúc oracle bên dưới.
Không tạo sẵn file giả để tránh SKIP. Biến môi trường PowerShell có sẵn được ưu tiên hơn `.env`.

DOM lưu tại `results/pdp_evidence/timeout_20261102_192919_391583.json` ghi nhận
sản phẩm JKA474, ba nhãn màu **Đen V2**, **Xám đậm V2**, **Be** (query tương ứng
`den-v2`, `xam-dam-v2`, `be`). Đây là bằng chứng cũ, cần xác minh lại.
Panel ghi Đen V2, giá `899.000đ`, size M/L/XL/2XL/3XL enabled dù URL đang là `color=be`:
ảnh chụp DOM có thể nằm trong lúc chuyển trang. Không dùng snapshot này làm oracle cho Be,
không suy rộng giá/tồn kho sang các màu khác. Chưa đủ bằng chứng gallery để lập oracle hoàn chỉnh.

Thu thập thủ công trên Windows (browser có giao diện, không chạy song song test):

```powershell
$env:HEADLESS='false'
python tools/inspect_pdp_variants.py
```

Chọn từng màu, chờ tên màu/URL/gallery đồng bộ, kiểm tra ảnh đúng màu bằng mắt rồi Enter
ở terminal để lưu JSON và screenshot. Thu thập cùng viewport với test. Kiểm tra cả ảnh lazy-load;
`images` trong oracle phải khớp toàn bộ tập currentSrc mà helper đọc, không chỉ ảnh swatch.
Đối chiếu giá nguyên văn và từng size (false = khả dụng, true = disabled), lập file oracle
độc lập sau khi duyệt bằng chứng. Ghi người duyệt/thời điểm bên ngoài JSON. Script chỉ thu thập,
không tự chuyển actual thành expected, không ghi `.env`.

PDP-03: fallback size đã thu hẹp về `#product-detail-variants ul li button`;
lọc nhãn size vẫn giữ nguyên. DOM cũ không có aria-pressed/aria-selected/aria-checked/data-state
trên size; M có đúng token `bg-neutral-900 text-light`, các size còn lại chỉ có token hover.
Helper giữ quy tắc token chính xác đã có bằng chứng, không dùng substring hoặc computed background.
Mỗi click chờ **selected_labels == [nhãn mới]** bằng WebDriverWait và lưu trước/sau vào
`results/pdp_evidence/variant_*.json`, gồm native is_selected, bốn thuộc tính trạng thái,
class và HTML. Assertion PDP-03 được giữ nguyên. Nếu hai nút thực trong đúng nhóm vẫn selected,
test timeout/FAILED; đối chiếu tiêu đề kích thước và giao diện để phân biệt lỗi site với helper.
Chưa tái hiện được M+3XL trong môi trường Codex do WinError 10013; không kết luận đã PASS.

```powershell
python tools/run_pdp.py -k PDP_01 -x
python tools/run_pdp.py -k 'PDP_02 or PDP_03'
```

## Tình trạng và cách chạy an toàn

Không có bản đầy đủ Bảng 4.11 trong yêu cầu; module bám theo mười mô tả được cung cấp.
Không có quyết định PASS thủ công nào được tạo sẵn.

Kết nối Python tới Coolmate trong môi trường triển khai bị chặn `WinError 10013`.
Công cụ web đọc được URL thực tế `https://www.coolmate.me/product/quan-dai-nam-double-knit`:
tên Quần dài Nam Double Knit, mã PAB438, các nút M/L/XL/2XL/3XL và hướng dẫn size.
Đây chỉ là **ứng viên**, chưa xác minh còn hàng, giá, màu, giới hạn hay khả năng đặt vào giỏ.
Không điền URL này thành dữ liệu còn hàng mặc định. Chưa tìm được biến thể hết hàng/sale đã xác minh.
Tất cả CSS trong `ProductDetailsMixin.LOCATORS` là locator ứng viên, chưa được kiểm tra bằng Selenium DOM.
Không coi văn bản trang do công cụ web trích xuất là xác nhận CSS.

Chạy tại thư mục gốc bằng PowerShell:

```powershell
python -m pip install -r requirements.txt
python tools/run_pdp.py --collect-only
python tools/run_pdp.py --offline
# Sau khi bổ sung dữ liệu vào .env hiện tại và xác nhận DOM:
python tools/run_pdp.py
# Chạy PDP-01 trước khi chạy toàn bộ:
python tools/run_pdp.py -k PDP_01 -x
Import-Csv results/pdp_test_results.csv | Format-Table
Start-Process (Resolve-Path results/pdp_report.html).Path
```

**Dùng entry point này**: root `conftest.py` có hook xóa `results/results.csv`, còn pytest.ini có
HTML mặc định `results/report.html`. Entry point dùng `--noconftest`, xóa addopts cho riêng tiến trình,
đăng ký plugin PDP và nhập lại đúng fixture `driver` hiện hữu. Không sửa hook/fixture chung.
Không dùng `pytest tests/test_chi_tiet_san_pham.py` nếu cần bảo toàn report chung.
Chạy từng phiên tuần tự; không dùng xdist hoặc hai tiến trình PDP cùng lúc.

Mỗi test tự động lấy một browser mới từ fixture hiện có; thiếu URL thì SKIP trước khi tạo browser.
Lỗi driver, timeout hoặc locator bắt buộc là lỗi thật, không đổi thành SKIP.
`--offline` ghi SKIP thật, không kiểm chứng chức năng UI. Collection không ghi báo cáo.
CSV mới nhất có đúng `Test_ID,Status,Duration,Timestamp,Browser`; PDP-06 có hậu tố `[1]`…`[abc]`.
Duration cộng setup/call/teardown. FAIL ưu tiên hơn SKIP/PASS, kể cả lỗi teardown.
HTML tự chứa, mở trực tiếp, có lý do SKIP và cột phân biệt Manual/Automation.
Report PDP được thay bằng phiên mới nhất; không sửa CSV/HTML REG, LOG và report chung.
Ảnh lỗi chỉ bật qua `PDP_FAILURE_SCREENSHOTS=true` trong browser ẩn danh không có dữ liệu cá nhân;
mặc định tắt, không chụp page source/cookie/input. Không mua hàng hoặc thanh toán.

## Chuẩn bị dữ liệu và locator

Bổ sung vào `.env` đang có, không sao chép đè file:

| Biến | Điều kiện |
|---|---|
| PDP_URL_IN_STOCK | URL PDP thực tế, có >=2 màu và >=2 size còn hàng nếu dùng chung PDP-01/02/03 |
| PDP_URL_SOLDOUT | URL có ít nhất một size hết hàng trong màu được kiểm tra |
| PDP_SOLDOUT_SIZE | Nhãn size hết hàng chính xác |
| PDP_SOLDOUT_COLOR | Nhãn màu chính xác nếu tồn kho phụ thuộc màu (để trống khi không cần) |
| PDP_URL_SALE | URL sale đã kiểm tra, dành cho PDP-07 Manual |
| PDP_VARIANT_EXPECTATIONS | Đường dẫn JSON oracle được xác minh độc lập, dùng PDP-02 |
| PDP_LOCATORS_FILE | Tùy chọn đường dẫn JSON override CSS đã kiểm tra trên DOM hiện tại |

DevTools: kiểm tra mỗi CSS trong `pages/pdp_support.py`; scope về đúng chi tiết sản phẩm,
không lấy giá/ảnh/size từ gợi ý, header hoặc quick-add. `name`, `sku`, `price`, `description`,
`information` phải đọc được nội dung thực, không chỉ heading trống. `images` chỉ ảnh sản phẩm đã tải.
`colors`, `sizes` phải trỏ đúng phần tử click được và có nhãn duy nhất qua data-value/aria-label/title/text.
Xác minh selected dùng checked/aria-checked/aria-pressed/data-state hoặc class selected/active/is-selected/is-active;
disabled dùng native/aria-disabled hoặc class disabled/soldout/sold-out/is-disabled.
Nếu DOM dùng quy tắc khác, cập nhật tối thiểu helper PDP tương ứng sau khi khảo sát; CSS override không
thay đổi thuật toán đọc trạng thái. Không dùng JS để ép trạng thái hoặc click.

Ví dụ **cấu trúc** locator override, phải thay bằng CSS thực tế, không dùng nguyên mẫu:

```json
{"sku": "[data-testid='product-sku']", "cart_count": "[data-testid='cart-count']"}
```

`cart_count` phải là số lượng đáng tin cậy, hiển thị cả số 0. Thiếu badge không đồng nghĩa giỏ rỗng.
Nếu site chỉ có cart drawer, cần bổ sung cách đọc số lượng từ drawer sau khi khảo sát DOM;
hiện tại timeout là chưa kiểm chứng được, không PASS. Kiểm tra giỏ sau reload để đối chiếu trạng thái lưu.
`recommendations` chỉ scope khối gợi ý/combo, anchor tên phải đúng tên sản phẩm (không gồm giá/tag).
Liên kết rỗng, khối không tồn tại hay locator chưa xác nhận được ghi SKIP và cần đối chiếu Manual.

Oracle màu phải được thu thập độc lập bằng thao tác thủ công, ghi ngày kiểm tra ngoài JSON.
Không tạo oracle bằng cách copy giá trị ngay trong test đang chạy. JSON theo cấu trúc sau
(các giá trị minh họa không phải dữ liệu Coolmate):

```json
{
  "url": "https://www.coolmate.me/product/SLUG_DA_XAC_MINH",
  "colors": {
    "NHAN_MAU_THUC_TE": {
      "price": "GIA_HIEN_THI_THUC_TE",
      "images": ["https://MEDIA_URL_DA_XAC_MINH/anh.jpg"],
      "sizes": {"M": false, "L": false, "XL": true}
    }
  }
}
```

`sizes` ánh xạ nhãn sang **disabled**; khai đủ size và tất cả màu còn hàng. `images` là tập URL
currentSrc của các ảnh đang hiển thị trong gallery ở viewport chạy test. Giá giữ nguyên định dạng UI.
Giá bằng nhau giữa hai màu được chấp nhận. Oracle thiếu/sai khác UI là thất bại cần điều tra,
không tự cập nhật oracle để làm test PASS.

## Phạm vi Automation và phần A+M

| ID | Automation | Manual bổ sung/điều kiện |
|---|---|---|
| PDP-01 | Tên, mã, giá số, ảnh đã tải, mô tả, thông tin, size khả dụng, chọn biến thể và nút Add khả dụng | Kiểm tra bố cục/chất lượng nội dung và đúng sản phẩm |
| PDP-02 | Từng màu còn hàng, selected duy nhất; giá/ảnh/tập size đối chiếu oracle độc lập | Kiểm tra ảnh đúng màu bằng mắt; cập nhật oracle có kiểm soát |
| PDP-03 | Lần lượt mọi size khả dụng rồi quay lại size đầu; chỉ một selected | Kiểm tra hiển thị trạng thái và size khác nếu tồn kho đổi |
| PDP-04 | Biến thể disabled, pointer click thật không chọn được; Add bị chặn hoặc có lỗi, giỏ không đổi sau reload | Nếu size còn hàng được chọn sẵn và giữ lại sau click disabled: SKIP nhánh Add, người kiểm thử xác nhận dòng/biến thể trong giỏ |
| PDP-05 | Phát hiện thuộc tính thiếu, Add báo chọn thuộc tính, giỏ không đổi sau reload | Site tự chọn đủ thuộc tính hoặc Add disabled không có lời nhắc: SKIP, ghi hành vi thực; không xóa selection bằng JS |
| PDP-06 | CSV 1/2/5/0/-1/99999/abc, nhập bàn phím/blur, native validity/min/max, phản hồi và +/- nếu có | Nếu không có input: kiểm tra +/-; nếu không công bố max: chưa kết luận 99999, SKIP bộ dữ liệu đó |
| PDP-07 | SKIP Manual | Checklist giá sale bên dưới |
| PDP-08 | SKIP Manual | Checklist gallery bên dưới |
| PDP-09 | Click liên kết gợi ý có tên, kiểm tra đích URL và tên/thông tin PDP; hỗ trợ tab mới | Không có khối/không xác nhận được selector: SKIP có lý do; kiểm tra combo nhiều sản phẩm bằng tay |
| PDP-10 | SKIP Manual | Checklist size guide bên dưới |

PDP-06 không bấm Add với số lượng lớn. Nếu website chỉ kiểm tra tồn kho khi thêm giỏ,
cần chạy phần Manual trên sản phẩm đã xác minh, quan sát cảnh báo và số lượng thật trong giỏ.
Không suy ra tồn kho từ thuộc tính max nếu site chỉ dùng nó làm giới hạn giao diện.
1/2/5 phải được chấp nhận khi nằm trong min/max thực tế; ngoài giới hạn phải có chặn/lỗi/điều chỉnh.
99999 được chấp nhận nếu max thực tế cho phép; không có max thì ghi chưa kiểm chứng.
abc bị chặn, rỗng kèm native invalid hoặc tự điều chỉnh hợp lệ đều cần ghi hành vi thực tế.
Nút +/-: tăng/giảm đúng step; không xuống dưới min, không vượt max; giữ hoặc disabled ở biên.

## PDP-07 — Giá sale (Manual, chưa thực hiện)

Tiền điều kiện: PDP_URL_SALE thực sự đang sale; ghi thời điểm, biến thể, điều kiện voucher/thành viên.

| Bước | Expected Result | Actual Result | Trạng thái / bằng chứng |
|---|---|---|---|
| Mở PDP sale, xác nhận tên/mã | Đúng sản phẩm đã chọn, không phải listing/trang lỗi | | Chưa chạy |
| Quan sát giá gốc và giá giảm | Cả hai đọc được, phân biệt rõ; giá gốc > giá giảm > 0, cùng đơn vị | | Chưa chạy |
| Đối chiếu % giảm | (Giá gốc - giá giảm)/giá gốc × 100 khớp % hiển thị theo quy tắc làm tròn thực tế | | Chưa chạy |
| Đổi màu/size rồi quay lại | Giá/% đúng biến thể và điều kiện khuyến mãi; không bắt buộc đổi giá | | Chưa chạy |

Không tự PASS nếu thiếu giá gốc/% giảm; ghi chênh lệch, điều kiện áp dụng và chuyển cho người phụ trách.

## PDP-08 — Gallery (Manual, chưa thực hiện)

Tiền điều kiện: sản phẩm có nhiều ảnh, ghi tên/mã/màu đang chọn và viewport.

| Bước | Expected Result | Actual Result | Trạng thái / bằng chứng |
|---|---|---|---|
| Mở PDP, đợi ảnh tải xong | Ảnh không vỡ/trắng/mất phần sản phẩm, đúng tên và màu | | Chưa chạy |
| Bấm next/previous hoặc vuốt bằng thao tác được hỗ trợ | Đổi đúng ảnh, không kẹt; biên đầu/cuối theo thiết kế | | Chưa chạy |
| Chọn từng thumbnail rồi quay lại ảnh đầu | Ảnh chính tương ứng, thumbnail selected đúng và duy nhất | | Chưa chạy |
| Click ảnh/nút zoom nếu có | Zoom/modal mở đúng ảnh, nét và đọc được, không bị overlay che | | Chưa chạy |
| Đóng zoom và đổi màu | Trở lại PDP, gallery đúng màu/biến thể; tương tác tiếp được | | Chưa chạy |

Không có zoom/thumbnail thì ghi N/A và lý do, không tự kết luận PASS cho chức năng chưa tồn tại.

## PDP-10 — Hướng dẫn size (Manual, chưa thực hiện)

| Bước | Expected Result | Actual Result | Trạng thái / bằng chứng |
|---|---|---|---|
| Mở PDP và bấm Hướng dẫn chọn size | Đúng bảng/modal cho loại sản phẩm, không phải nội dung không liên quan | | Chưa chạy |
| Đọc bảng/hình size, cuộn nội dung nếu cần | Chữ/hình đọc được, đủ cột/đơn vị/size; không cắt/mờ hoặc lỗi ảnh | | Chưa chạy |
| Đóng bằng nút đóng; thử Escape/ngoài modal nếu thiết kế hỗ trợ | Modal đóng, overlay biến mất, PDP tương tác lại được | | Chưa chạy |
| Mở lại rồi đóng lần hai | Nội dung vẫn đúng, không nhân đôi modal, không kẹt focus/overlay | | Chưa chạy |

Thiếu liên kết hướng dẫn thì ghi N/A hoặc lỗi theo đặc tả đã thống nhất, không tự PASS.

## Phiếu ghi nhận chung (dùng thêm cho mọi phần A+M)

| Test ID / dữ liệu con | URL / tên / mã / màu / size | Ngày giờ / browser / viewport | Expected | Actual | PASS/FAIL/SKIP/N/A | Người kiểm thử / bằng chứng |
|---|---|---|---|---|---|---|
| | | | | | Chưa chạy | |

Lưu phiếu thủ công riêng; không sửa CSV tự động thành PASS cho test Manual chưa chạy.
Khi thất bại, ghi rõ lỗi nghiệp vụ hay chưa xác minh locator/dữ liệu; không dùng tài khoản có dữ liệu riêng.
