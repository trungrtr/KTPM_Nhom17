# Xuất báo cáo tổng hợp REG

## CSV tổng hợp tự động sau Pytest

```powershell
python -m pytest tests/test_dang_ky.py -v -rs
Import-Csv results\reg_test_results.csv | Format-Table -Wrap
Import-Csv results\reg_pytest_raw.csv | Format-Table -Wrap
Start-Process results\reg_tong_hop.html
```

Hook `utils/reg_reporting.py` tự ghi raw theo từng lượt test (gồm kết quả
setup/call/teardown trong `Phases`), rồi xuất 14 dòng tổng hợp khi session kết
thúc. `reg_test_results.csv` có Status tổng hợp và Auto_Status/Manual_Status
riêng. Auto lỗi setup/teardown được ghi failed, với pha cụ thể trong raw.
Auto failed không bị Manual che mất; Status giữ failed (auto) và Notes giải
thích khác biệt. Dòng chỉ Passed Manual để trống Duration/Timestamp/Browser
vì không biết thời điểm/thời lượng kiểm thử thủ công. Thời gian Selenium vẫn
giữ trong raw. Không gán thời điểm xuất báo cáo thành thời điểm chạy Manual.

Chạy collect-only hoặc module khác không cập nhật các CSV REG. Chạy REG một
phần sẽ vẫn xuất 14 dòng, nhóm chưa chạy ghi chưa có kết quả Auto, không lấy
PASS từ lần trước. Mỗi lần chạy REG sao lưu CSV cũ trong `reg_run_history`;
báo cáo tổng hợp và bản sao raw lưu thêm trong `reg_report_history`.

Nếu cần tạo lại báo cáo mà không chạy Selenium:
`python tools\export_reg_report.py` (ưu tiên raw REG mới nhất).

Các hướng dẫn dưới đây về nguồn CSV/HTML áp dụng khi chưa có raw mới, hoặc
khi chỉ định rõ `--source`; không dùng CSV tổng hợp làm log Selenium.

Sau mỗi lần Pytest chạy xong, từ thư mục gốc dự án:

```powershell
$env:PYTHONIOENCODING='utf-8'
python tools\export_reg_report.py
Import-Csv results\reg_tong_hop.csv | Format-Table -Wrap
Start-Process results\reg_tong_hop.html
```

Script ưu tiên `results/reg_pytest_raw.csv` khi file này tồn tại; nếu chưa có
raw, chọn file mới nhất giữa `results/report.html` và `results/results.csv`. Không lấy PASS từ báo cáo
tổng hợp cũ, không bù bằng kết quả một lần chạy trước khi lần chạy mới thiếu REG.
HTML pytest-html có trạng thái cả lỗi setup/teardown; CSV hiện tại chỉ ghi pha
call nên HTML thích hợp hơn khi cần xem lỗi fixture.

Chọn rõ CSV/HTML của một lần chạy khi cần:

```powershell
python tools\export_reg_report.py --source results\reg_pytest_raw.csv
```

Mỗi nhóm một dòng. Chỉ Auto Passed khi tất cả lượt được ghi nhận đều Passed và
đủ số lượt tham số của bộ hiện tại: REG-03=4, REG-04=5, REG-05=4, REG-09=2,
REG-11=4, các nhóm khác=1. Nhóm thiếu dữ liệu không tự nhận Auto PASS.
Failed/Error Auto được giữ và nêu khác biệt nếu có Manual PASS.

Manual REG-01/03/06/07/11/12/13/14 dựa trên lời xác nhận kiểm thử thành công của
người dùng trong yêu cầu, không phải ảnh chứng minh mới hay lần chạy Selenium.
REG-10 chỉ ghi N/A khi có bản kiểm tra DOM `reg_dom_inspection.json` cho thấy
form không có trường xác nhận mật khẩu; trạng thái Auto vẫn giữ nguyên.

Các file `reg_test_results.csv` và `reg_tong_hop.html/csv` được cập nhật. Trước khi cập nhật, phiên bản
tổng hợp cũ được sao lưu vào `results/reg_report_history/<timestamp>/`.
Thư mục đó cũng giữ báo cáo mới, bản sao nguồn Auto và SHA256 của nguồn để
truy vết. Test, hook Pytest và các log/HTML gốc không bị chỉnh sửa.

`tools/run_reg_review.py` dùng cùng bộ xuất này; `--run` vẫn chỉ chạy REG-09/10
trong bản sao cô lập. Báo cáo từ lần chạy giới hạn đó sẽ không tự bổ sung PASS
của những REG chưa chạy.

Các file `reg_summary.*` và `REG_REVIEW.md` có trước là báo cáo lịch sử của lần
đối chiếu trước; báo cáo hiện tại là `reg_tong_hop.*`.
