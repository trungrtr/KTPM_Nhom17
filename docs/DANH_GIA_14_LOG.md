# Đánh giá 14 test case LOG — Coolmate

Ngày đánh giá: 31/10/2026. Phạm vi: phân tích tĩnh source hiện tại và bằng chứng chạy đã lưu. Chỉ tạo báo cáo này; không sửa code, dữ liệu, REG, LOG-01 hoặc báo cáo cũ. Không đọc `.env`, không chạy pytest, không gửi yêu cầu đăng nhập/khôi phục, không truy cập website trong lần đánh giá này.

## 1. Nguồn bằng chứng và tổng quan

Đã đọc `tests/test_dang_nhap.py`, `pages/login_page.py`, `pages/base_page.py`, hai `conftest.py`, `utils/config.py`, `pytest.ini`, CSV và HTML LOG. Đọc bổ sung có giới hạn: `docs/LOG_TESTS.md` để xác định tiền điều kiện/Bảng 4.8; `utils/driver_factory.py` để xác định vòng đời browser; phần cookie của `pages/register_page.py`; JSON chẩn đoán phiên 12:28–12:29 trong `results/log_session_fix`; CSV LOG-01 tại `results/log_popup_fix` để đối chiếu lịch sử. Không dùng bản backup source làm đại diện cho source hiện tại.

Không tìm thấy tài liệu gốc chứa Bảng 4.8 trong danh sách file dự án (kể cả PDF/DOCX/XLSX). `docs/LOG_TESTS.md` tự tham chiếu Table 4.8 nhưng không chứa bảng gốc. Do đó đối chiếu yêu cầu theo đúng 14 mục người dùng cung cấp; chưa chứng minh được tính tương đương tuyệt đối với bảng gốc về dữ liệu, thông báo và chính sách.

| Nguồn | Thời điểm | Kết quả lưu | Ý nghĩa và giới hạn |
|---|---|---|---|
| `results/log_report.html` | Generated 31-Oct-2026 11:13:06 | 14 node: 2 PASS (03,04), 11 FAIL, 1 SKIP (10) | Phiên đầy đủ cũ; traceback chứa helper cũ và số dòng khác source hiện tại. Không xác nhận kết quả bản code hiện tại. |
| `results/log_test_results.csv` | 12:28:49–12:29:26 ngày 31/10 | 5 dòng: 1 PASS, 4 FAIL, 0 SKIP | Chỉ LOG-02, hai nhánh LOG-09, LOG-12, LOG-13. Không phải lần chạy đủ 14 LOG. |
| JSON LOG-01 | 12:28:11 | Có `LOGOUT`, `ACCOUNT_LINK`, không có form login/challenge | Bằng chứng UI xác thực mạnh hơn redirect; JSON không phải kết quả pytest. |
| CSV phụ `log_popup_fix/log_test_results.csv` | 11:56:01 | LOG-01 SKIP, 5.801 giây | Lịch sử khác phiên; không dùng để phủ định PASS được người dùng thông báo. |

LOG-01 được người dùng xác nhận đã PASS: giữ nguyên trạng thái đã xác nhận đó và không đề xuất chỉnh sửa test. Tuy nhiên, CSV chính hiện không chứa dòng PASS LOG-01; HTML cũ ghi FAIL. Cần giữ rõ nguồn khi công bố kết quả, không suy ra PASS pytest chỉ từ JSON 12:28:11.

CSV gần nhất: LOG-02 FAIL 15.452s; LOG-09 email FAIL 9.585s; LOG-09 mật khẩu PASS 7.406s; LOG-12 FAIL 9.951s; LOG-13 FAIL 9.708s. Cả năm dòng ghi Browser=`unavailable`. Điều này không chứng minh không có browser: JSON cùng thời điểm thể hiện DOM/URL và trạng thái trang. Tổng Duration CSV là 52.102s, tổng các pha theo hook; không phải thời lượng toàn phiên. Thời gian trong HTML hiển thị làm tròn và thuộc phiên khác. HTML ghi “13 tests took 00:02:43” trong khi dữ liệu chi tiết có 14 node và bộ đếm là 11 Failed + 2 Passed + 1 Skipped; cần giữ nguyên sự khác biệt này khi trích báo cáo, không coi dòng run-count là số mã được bao phủ.

Source hiện có **15 hàm test cho 14 mã LOG**, do LOG-09 đã tách thành hai hàm. Không được tính PASS của nhánh mật khẩu là PASS toàn LOG-09. Các trạng thái trong bảng dưới là lịch sử quan sát được, không phải xác nhận chạy lại source hiện tại.

## 2. Đánh giá từng LOG

Các rủi ro dùng chung về cookie, COOL CLUB, locator và wait ở mục 3 áp dụng cho mọi dòng. “Đáp ứng” ở đây mô tả chất lượng thiết kế test, không khẳng định website đúng/sai.

| Mã / mục tiêu | Mức đáp ứng của code và assertion | Trạng thái gần nhất có bằng chứng | Nguyên nhân, nguy cơ PASS/FAIL giả và đề xuất |
|---|---|---|---|
| LOG-01 — email/mật khẩu đúng, hiển thị tài khoản | Tốt về xác nhận phiên: lấy credentials bắt buộc, `authenticated(timeout)` rồi mở account và kiểm tra lại (test dòng 105–122). Không chấp nhận trang chủ đơn thuần. Chưa đối chiếu danh tính tài khoản mong đợi. | PASS theo người dùng; HTML 11:13 FAIL cũ; JSON 12:28:11 có LOGOUT, ACCOUNT_LINK, không challenge. Không có dòng pytest PASS tương ứng trong CSV chính. | FAIL cũ tại nhận diện auth, không chứng minh sai chức năng. JSON mới hỗ trợ nhận diện phiên nhưng không thay kết quả runner. COOL CLUB chỉ là tín hiệu ứng viên; locator chưa xác minh đầy đủ. **Giữ nguyên test đã PASS**, chỉ bổ sung truy vết bằng chứng trong lần chạy sau. |
| LOG-02 — SĐT/mật khẩu đúng | Đúng luồng; `TEST_PHONE` dùng chung `TEST_PASSWORD`, yêu cầu số đã liên kết cùng tài khoản. `assert_logged_in` yêu cầu account được bảo vệ, tốt hơn redirect; chưa kiểm tra danh tính. | CSV FAIL 12:28:49, 15.452s; HTML cũ timeout ở `wait_result`. | JSON 12:28:42: trang chủ, một generic error, không form/auth/challenge; JSON 12:28:46 không còn error. Chưa có traceback mới tương ứng để xác định điểm fail chính xác. Không thể gọi đây là lỗi SĐT; có thể nhận diện UI, chờ hoặc dữ liệu. P0 xác minh account/SĐT và tín hiệu auth; P1 gắn lỗi đúng form, không coi generic alert trên trang chủ là từ chối đăng nhập. |
| LOG-03 — mật khẩu sai | Đúng mục đích: mật khẩu đúng nối UUID, kiểm tra không auth, form còn hiện và có lỗi; loại field error khỏi credential rejection. Chưa assert lỗi đúng nghĩa sai thông tin. | HTML PASS ~7s; không có lượt mới trong CSV. | PASS chỉ chứng minh helper cũ thỏa điều kiện, không xác nhận nội dung lỗi hoặc bản hiện tại. Mật khẩu nối UUID có thể vượt giới hạn độ dài/cắt chuỗi, khiến không còn là ca sai mật khẩu hợp lệ. Generic alert bất kỳ có thể gây PASS giả. P1 dùng dữ liệu sai nhưng đúng độ dài/định dạng và kiểm tra phản hồi credential được chấp thuận. |
| LOG-04 — tài khoản không tồn tại | Đọc `LOG_NONEXISTENT_EMAIL`; cùng helper rejection như 03. Không tự chứng minh email chưa đăng ký; không kiểm tra thông báo phù hợp. | HTML PASS ~6s; CSV mới không có. | Chỉ đủ bằng chứng UI rejection theo helper cũ. Một email thực sự tồn tại với mật khẩu sai cũng có thể PASS. P1 xác nhận dữ liệu bằng quy trình quản lý account; chấp nhận thông báo chung chống dò tài khoản nếu đó là chính sách, không bắt buộc lộ tài khoản không tồn tại. |
| LOG-05 — trống cả hai | Kiểm tra giá trị rỗng, submit, không auth và có native/ARIA error từng trường. Không dùng riêng nút disabled để PASS. | HTML FAIL ~15s tại `wait_result`. | Không thấy bằng chứng mà locator/helper cũ hỗ trợ, chưa chứng minh site thiếu validation. Native validation có thể chỉ báo trường đầu tiên; disabled button có thể là UX dự kiến. P1 khảo sát trạng thái thực, phân biệt required với lỗi khác, xác nhận yêu cầu có bắt buộc báo đồng thời hai trường hay không. |
| LOG-06 — trống mật khẩu | Nhập email, kiểm tra riêng password rỗng và field error. Chưa assert loại `valueMissing`/nội dung required hoặc email được chấp nhận. | HTML FAIL ~15s tại `wait_result`. | Có thể thiếu native/ARIA mapping hoặc nút disabled, chưa kết luận website. Field-specific evidence là điểm tốt; lỗi bất kỳ của password vẫn có thể thỏa assertion. P1 xác minh error liên kết đúng password, required và không phát sinh lỗi email ngoài dự kiến. |
| LOG-07 — trống định danh | Nhập password, yêu cầu error riêng identity và không auth. Chưa phân loại chính xác required. | HTML FAIL ~17s tại `wait_result`. | Cùng giới hạn 05/06. P1 khảo sát locator/error mapping trường email/SĐT; kiểm tra thông báo bắt buộc đúng trường và dữ liệu password hợp lệ. |
| LOG-08 — email sai định dạng và khoảng trắng | Có bốn mẫu sai và một email đúng có khoảng trắng hai đầu (239–249). Mẫu sai chỉ gọi `assert_rejected(...identity...)`, chưa bắt buộc `field_errors(identity)` hoặc loại lỗi format; nhánh spaces cần login thành công. | HTML FAIL ~22s ngay vòng malformed; không chứng minh nhánh trim đã chạy. | Generic error có thể khiến format PASS giả. Browser/input có thể tự chuẩn hóa khoảng trắng trước server, nên PASS chỉ chứng minh hành vi end-to-end, không chứng minh server trim. P1 tách từng mẫu sai và leading/trailing/both spaces để không mất coverage khi ca đầu fail; ghi nhận value đã chuẩn hóa dưới dạng boolean, không lưu email. Các lần load giữa vòng chưa có guard trước nhập nếu challenge xuất hiện mới. |
| LOG-09 — email không phân biệt hoa/thường; password có phân biệt | Hiện đã tách hai hàm: email `.upper()` đúng password; password `.swapcase()` đúng email. Có SKIP khi biến đổi không tạo dữ liệu khác. Cả hai dùng account mới theo fixture. | CSV: email FAIL 12:28:59; password PASS 12:29:06. Toàn LOG-09 **chưa đạt**. | JSON email: trang chủ, generic error, không auth/challenge; chưa biết nội dung/nguyên nhân. JSON password: form login, một error thuộc nhóm “không chính xác”, không auth/challenge, hỗ trợ rejection. PASS mật khẩu chưa đủ khẳng định case-sensitive nếu account gốc không đăng nhập được trong cùng bối cảnh. P1 giữ tách nhánh, gắn tên nhánh vào CSV, kiểm chứng baseline account và trường hợp email mixed/lower theo yêu cầu gốc. |
| LOG-10 — bảo vệ sau năm lần sai | Dùng account riêng; chặn trùng email chính; tối đa năm vòng, dừng/SKIP khi bảo vệ sớm. Lần 5 yêu cầu challenge hoặc từ khóa khóa/rate limit, rồi không auth. Đúng hướng quan sát cơ chế thực tế nhưng áp đặt phải có biểu hiện ở lần 5. | HTML SKIP 1ms: thiếu `LOG_LOCKOUT_EMAIL`; CSV mới không có. | Lỗi tiền điều kiện, chưa thử cơ chế bảo vệ. Không suy ra thiếu bảo mật nếu không có thông báo ở lần 5; cần chính sách được xác nhận. Từ khóa chung có thể PASS giả; UUID quá dài và reload có thể thay đổi đường đi; không chứng minh đủ năm request server thực nhận. P0 không tự chạy; P1 chốt ngưỡng/phạm vi/cooldown và account được phép. CAPTCHA ở đây chỉ là bằng chứng bảo vệ, không phải PASS validation. |
| LOG-11 — ẩn/hiện password | Tốt cho hành vi cốt lõi: ban đầu password, chuyển text rồi password; wait kiểu input và bảo toàn value. Không submit nên không cần login. | HTML FAIL ~15s khi `BasePage.clickable(PASSWORD_TOGGLE)`. | Timeout chưa chứng minh nút hỏng. `visible` chọn phần tử hiện, nhưng `clickable` kế thừa chọn match đầu nên bản ẩn responsive có thể gây FAIL giả. P1 xác minh locator toggle và chọn control thuộc input đang hoạt động; chạy riêng. Cookie/overlay có thể chặn click; chưa có bằng chứng COOL CLUB liên quan ở ca này. |
| LOG-12 — logout, Back không phục hồi phiên | Có login độc lập, logout, Back, readyState, phủ định auth; sau đó mở account và yêu cầu login (313–325). Đúng luồng chính nhưng thiếu kiểm tra dữ liệu riêng tư ở trang Back và server invalidation. | CSV FAIL 12:29:16; HTML cũ fail ở tiền điều kiện login, chưa logout. | JSON mới login-result 12:29:12 chưa có auth, một generic error; không có bằng chứng hoàn tất logout/Back. Không kết luận lỗi logout. `logout()` chờ “không auth” có thể đúng tạm thời lúc chuyển trang; phủ định auth không đồng nghĩa không hiển thị dữ liệu từ cache. P0 khôi phục tiền điều kiện; P1 kiểm tra trang được bảo vệ sau refresh/Back và dữ liệu cá nhân không còn hiện, phân biệt BFCache với phiên server. |
| LOG-13 — reload, tab mới giữ phiên | Login độc lập, refresh đợi auth; tab mới mở account và cần auth; finally đóng tab. Bao phủ cùng browser context, chưa kiểm tra hết hạn/đóng browser/remember-me. | CSV FAIL 12:29:26; HTML cũ fail ở login, chưa tới reload/tab. | JSON mới login-result 12:29:21 không auth/challenge, có generic error; chưa kiểm chứng duy trì phiên. P0 xác nhận login trước. P1 đối chiếu chính sách thực tế rồi kiểm tra auth ổn định và cùng account ở hai tab. Không mở rộng kết luận sang lưu phiên sau khởi động browser mới. |
| LOG-14 — quên mật khẩu: tồn tại, không tồn tại, trống | Có ba nhánh trong một hàm: rỗng cần field error, email đúng cần success text, email lạ chấp nhận generic success hoặc error. Không kiểm tra gửi/nhận thư hoặc reset token. | HTML FAIL ~22s ở `open_reset()` chờ `RESET_EMAIL`; chưa tới ba kết quả nghiệp vụ. | Locator form reset chưa xác nhận; không thể kết luận site quên mật khẩu hỏng. Email lạ có thể PASS do lỗi bất kỳ kể cả lỗi định dạng/dịch vụ; success role status có thể không liên quan. P1 tách ba ca; scope form reset; kiểm tra phản hồi đúng chính sách, không authenticated, không chấp nhận CAPTCHA là validation. Kiểm tra inbox một lần có kiểm soát nếu expected yêu cầu email được gửi; không gửi hàng loạt. |

## 3. Các vấn đề automation ảnh hưởng nhiều test

### 3.1. Nhận diện phiên và popup

`LoginPage._authentication_evidence` (154–173) loại trạng thái có cả form login hoặc challenge; chỉ chấp nhận logout control hoặc lời chào cá nhân trong COOL CLUB, lưu bằng chứng lời chào trong cùng document. Đây là cải thiện so với redirect/account link công khai. `assert_logged_in` (68–82) còn mở trang account để kiểm chứng; **trang chủ và ACCOUNT_LINK riêng lẻ không đủ chứng minh login**.

Tuy vậy, `Hi <tên>` và nút logout chỉ là bằng chứng UI, chưa ràng buộc danh tính/account mong đợi hay server authorization. Một popup cá nhân hóa lưu cache trong cùng document có thể giữ tín hiệu cũ; logout có chủ động xóa cache nhưng không bao quát mọi cách hết phiên. Các selector COOL CLUB yêu cầu đồng thời tiêu đề, skip và Hi; thay lời chào/ngôn ngữ/cấu trúc sẽ không match. `popup_locators_live_verified=false` trong JSON mới cho thấy chưa có xác minh trực tiếp. `popup_seen=false` không chứng minh site không có popup khác cấu trúc.

`authenticated(timeout=0)` không thực sự không chờ: có thể gọi wait lời chào và hai wait dọn popup tối đa 3s mỗi giai đoạn. Gọi nó trong wait/rejection/poll khiến thời gian lồng nhau vượt timeout danh nghĩa 10s, đồng thời có side effect đóng popup. Stale popup hoặc popup không có nút đóng phù hợp có thể gây FAIL automation. Dọn `PROFILE_SKIP` toàn document và `OFFER_CLOSE` gồm span/div tương đối rộng, cần chứng minh không chọn nhầm. Không nên coi mọi timeout popup là lỗi đăng nhập của website.

### 3.2. Locator và wait

- `visible()` LOG lấy phần tử đang hiện, khắc phục bản ẩn; nhưng `BasePage.clickable()` vẫn dùng match đầu. Ảnh hưởng toggle, forgot link và các click kế thừa. Chưa scope identity/password/submit vào cùng form nên nhiều form có thể bị ghép nhầm.
- `SUBMIT_BTN`, `RESET_SUBMIT`, `RESET_EMAIL`, `ERROR_MESSAGE`, `RESET_SUCCESS` rộng; `[role=alert]`, `.text-danger` và `[role=status]` có thể thuộc thành phần khác. JSON có generic error trên trang chủ nhưng không có category: không đủ gọi là “website rejected login” như thông điệp assertion hiện tại.
- `wait_result` (260–269) nhận ACCOUNT_LINK làm điều kiện hoàn tất. Nếu link có sẵn công khai, wait kết thúc trước phản hồi request; các assertion ngay sau đó có thể FAIL giả hoặc đọc lỗi cũ. Cần kết quả mới của lần submit, không chỉ phần tử tồn tại.
- `submit` trả False nếu disabled, nhưng hầu hết caller bỏ qua. Không có bằng chứng request đã gửi; nên phân biệt bị client chặn, server rejection và thao tác chưa diễn ra. Disabled không tự PASS và cũng chưa tự chứng minh lỗi site.
- Timeout cấu hình 10s, cookie 5s, popup 3s; không có page-load timeout riêng trong factory. `readyState=complete` không bảo đảm SPA hoàn tất trạng thái auth. Không nên chỉ tăng timeout để che thiếu điều kiện đồng bộ.

### 3.3. Cookie, CAPTCHA/OTP và validation

`BasePage.POPUP_CLOSE_LOCATORS=[]`. `LoginPage.load` mượn `RegisterPage.accept_cookies()` với text “Chấp nhận tất cả”, chờ clickable 5s rồi click; không chờ overlay biến mất. Không có banner sẽ tốn wait, còn cấu trúc/ngôn ngữ khác có thể để overlay lại. Đây là phụ thuộc REG khi chạy LOG nhưng không có lý do chỉnh REG trong đợt đánh giá này.

`challenge()` chỉ xét element đang hiện theo các selector iframe bframe/challenge, g-recaptcha, h-captcha và input otp. Widget hiện nhưng chưa yêu cầu giải có thể bị SKIP nhầm; challenge ở iframe/DOM khác hoặc cơ chế chặn không nằm trong selector có thể không được nhận ra. Guard thường chạy sau wait, không luôn ngay sau điều hướng trong các vòng lặp; LOG-01 assert auth trước guard sau login nên challenge xuất hiện lúc submit có thể thành FAIL thay vì SKIP. Ghi nhận hạn chế này, không chỉnh LOG-01 đã PASS.

`field_errors` dùng native validationMessage và ARIA-linked message khi invalid: tốt hơn bắt hint thường trực. Nhưng chưa phân biệt `valueMissing`, `typeMismatch`, pattern/length và lỗi server. Native error có thể tồn tại ngay khi nhập, trước submit, nên không chứng minh server xử lý. `assert_rejected` không có fields loại native/ARIA errors, nhưng một lỗi credential server gắn ARIA vào field cũng có thể bị loại nhầm thành client validation. Ngược lại, có fields chỉ đòi lỗi chung, yếu hơn required helper. Không được tính CAPTCHA là PASS LOG-05–08/14.

### 3.4. Độc lập và dữ liệu/môi trường

Fixture `driver` mặc định function scope, tạo Chrome mới và quit sau mỗi test; không dùng user-data-dir trong factory. Không thấy test nào dựa trực tiếp vào phiên browser test trước. LOG-12/13 tự login; LOG-09 hai nhánh độc lập. Tuy nhiên các ca dùng chung tài khoản, IP và dịch vụ nên vẫn chia sẻ lockout/rate-limit/trạng thái account phía server. LOG-10 riêng email chưa bảo đảm khác account nếu dùng alias; các ca sai khác cũng có thể góp ngưỡng bảo vệ. Không nên chạy song song mặc định.

`required()` chỉ kiểm tra biến có chuỗi không rỗng, không xác minh account hoạt động, liên kết phone, email không tồn tại hoặc whitespace-only. Không kiểm tra giá trị `.env` trong lần đánh giá này. `load_dotenv()` và biến môi trường có thể khiến hai máy dùng dữ liệu/locator khác nhau. Factory tải driver qua webdriver-manager, cần cache/quyền và kết nối. Tài liệu LOG ghi WinError 5/tab crashed ở phiên trước: chỉ là lịch sử môi trường, không áp dụng suy đoán cho mọi FAIL mới.

`login_driver` đổi lỗi tạo driver thuộc WebDriverException/RequestException/OSError thành SKIP, phù hợp tách hạ tầng nhưng có thể che cấu hình driver hỏng nếu tổng hợp SKIP như thành công. Mạng `net::ERR_` lúc load thành SKIP; các lỗi khác vẫn FAIL. SKIP không phải kết quả chức năng.

## 4. Chất lượng báo cáo và nguy cơ kết luận sai

Hook LOG reset CSV khi chọn bất kỳ test trong module, kể cả chạy subset: vì vậy lượt mới đã thay phiên đầy đủ bằng 5 dòng. CSV có tổng pha setup/call/teardown và ưu tiên failed rồi skipped là điểm tốt, nhưng thiếu nodeid/nhánh, run ID, phase, lý do và phiên bản source. Hai LOG-09 không phân biệt được nếu chỉ đọc CSV; việc ánh xạ nhánh trong báo cáo này dựa thứ tự hàm và JSON cùng thời điểm. `_LOG_REPORTS` trong process và ghi file trực tiếp chưa thiết kế an toàn cho nhiều worker.

Browser được lấy từ `item.funcargs`; fixture được lấy động qua `request.getfixturevalue` có thể không nằm ở nơi hook kỳ vọng. Cần kiểm chứng đường lấy browser khi sửa; không được suy ra “không khởi tạo được Chrome” từ `unavailable` trong CSV. HTML cũ chỉ có một LOG-09, helper cũ, cho thấy rõ lệch source; tài liệu nói “one row per LOG case” và “14 cases” đã không còn chính xác với 15 hàm.

Root hook chỉ ghi pha call, browser hardcode chrome; CSV chung không tương đương CSV LOG tổng pha. `pytest.ini` mặc định ghi `results/report.html`, không tự cập nhật `log_report.html`. Root `pytest_sessionstart` xóa CSV chung cả khi chạy LOG, nên không chạy pytest/collect-only để đánh giá khi cần bảo toàn báo cáo. `git status` báo thư mục không phải Git repository: không có căn cứ dùng Git diff để chứng minh lịch sử revision.

Chụp chứng cứ LOG có che input/text và JSON allowlist/redact là điểm tốt, nhưng ảnh bị che toàn chữ/ảnh nên rất hạn chế đọc nội dung lỗi. Root hook ảnh FAIL không che, có thể lưu danh tính hoặc password khi toggle; screenshot exception cũng chưa được bắt để bảo vệ reporting. Không đọc ảnh có nguy cơ lộ dữ liệu trong lần đánh giá này. Hàm `save_log01_evidence` được gọi trong teardown mọi test; phần ghi file ngoài try có thể biến lỗi lưu bằng chứng thành teardown FAIL. JSON failure diagnostic dùng tên cố định sẽ bị ghi đè; không thấy các file diagnostic đó ở thư mục results gốc khi kiểm tra. Vì vậy không thể tái dựng đầy đủ traceback mới chỉ bằng JSON phụ.

| Nguy cơ | Test bị ảnh hưởng | Cơ sở |
|---|---|---|
| PASS giả: lỗi chung thay lỗi đúng nghiệp vụ | 03,04,08,09-password,14-unknown | Chỉ yêu cầu messages/error hiện, chưa ràng buộc nguồn và nghĩa. |
| PASS giả: dữ liệu không chứng minh điều kiện đầu vào | 03,04,09-password,10 | Password quá dài, email chưa xác minh, thiếu baseline hoặc chưa đếm server request. |
| PASS giả: tín hiệu UI thay authorization/danh tính | Các ca thành công,12,13 | Logout/greeting cần chứng minh chỉ hiện khi thực sự có phiên; chưa đối chiếu user. |
| FAIL giả: wait kết thúc sớm hoặc locator bản ẩn | 02,05–09,11–14 | ACCOUNT_LINK public; clickable match đầu; form/error/reset selector rộng. |
| FAIL giả: chưa tới hành vi đang đánh giá | 12,13,14 | Bằng chứng dừng ở login hoặc mở form reset. |
| FAIL giả hoặc SKIP sai: challenge/popup chưa nhận diện | Các ca dùng login/reset | Selector chưa bao quát, wait lồng, guard không đồng nhất. |

Không có FAIL nào trong nguồn đã đọc đủ chứng minh độc lập một lỗi chức năng website. Có các lỗi kiểm thử/báo cáo xác định được từ code; có phản hồi UI từ chối ở nhánh password case; các nguyên nhân server còn lại chưa đủ bằng chứng.

## 5. Yêu cầu thiếu hoặc chưa kiểm chứng

- Bảng 4.8 gốc: nội dung thông báo, ngưỡng bảo vệ, chính sách trim và duy trì phiên chưa có nguồn độc lập xác nhận.
- Danh tính account hiển thị sau thành công; tính hợp lệ/liên kết SĐT; trạng thái email không tồn tại; password đúng tại thời điểm chạy.
- Required thực tế từng trường, format từng mẫu và từng chiều whitespace; không xác nhận client hay server chỉ từ generic message.
- Email case-insensitive chưa đạt bằng chứng; password case PASS ở nhánh riêng cần baseline cùng điều kiện.
- Năm lần sai và chính sách bảo vệ; CAPTCHA/OTP xuất hiện ở giai đoạn nào; chưa có kết quả thực tế LOG-10.
- Logout/Back và reload/tab chưa đi qua tiền điều kiện trong các bằng chứng FAIL; không xác nhận server invalidation hoặc dữ liệu cache.
- Ba nhánh reset chưa có kết quả nghiệp vụ trong HTML; UI success không chứng minh thư đến inbox hoặc liên kết reset dùng được.
- Chưa có một phiên đủ 15 node dùng đúng source hiện tại, cùng cấu hình, có traceback và bằng chứng được gắn run ID. Không tổng hợp trạng thái rời rạc thành tỷ lệ đạt hiện tại.

## 6. Danh sách sửa chữa đề xuất (chưa thực hiện)

| Ưu tiên | Công việc | Lý do và tiêu chí hoàn tất |
|---|---|---|
| P0 | Bảo toàn artefact và chuẩn hóa run ID/nodeid/nhánh/source version trước lần chạy tiếp | Không mất phiên đầy đủ khi chạy subset; phân biệt hai LOG-09, trạng thái từng phase và browser thật. |
| P0 | Xác minh read-only UI/account và dữ liệu dùng cho 02/09/12/13; hiệu chỉnh helper dùng chung sau review, giữ nguyên test LOG-01 đã PASS và REG | Gỡ chặn tiền điều kiện, phân biệt public link với phiên thật; generic alert ngoài form không còn quyết định login. Chạy lại LOG-01 chỉ để regression nếu helper đổi. |
| P0 | Chốt account/chính sách và quyền chạy LOG-10, giới hạn reset; bảo vệ artefact có thông tin nhạy cảm | Tránh khóa account chính, gửi thư lặp; không bypass challenge. Không tự kích hoạt LOG-10 từ lệnh full suite. |
| P1 | Scope locator theo form/control đang hiện; đồng bộ submit và phản hồi mới; popup/cookie có điều kiện kết thúc rõ | Giảm lỗi bản ẩn, overlay và wait kết thúc sớm; có evidence DOM đã che dữ liệu cho từng selector. Thực hiện trong LOG khi có thể, không sửa REG. |
| P1 | Phân biệt required/format/credential/protection; kiểm tra nghĩa thông báo và nguồn phản hồi | Chặn generic error PASS giả và ARIA server error FAIL giả; disabled/challenge được ghi nhận đúng loại. |
| P1 | Tách LOG-08 từng dữ liệu, LOG-14 ba nhánh; giữ LOG-09 hai nhánh; tăng chứng cứ Back/session | Một fail không làm mất coverage còn lại; trạng thái tổng LOG chỉ đạt khi mọi nhánh bắt buộc đạt. |
| P1 | Sửa đường lấy browser, báo lỗi capture an toàn, ảnh che dữ liệu ở mọi hook, lưu diagnostic theo run | Không có teardown/capture làm sai kết quả và không mất chứng cứ; không công bố file nhạy cảm. |
| P2 | Đồng bộ docs về 15 node, duration tổng pha và lệnh chọn test an toàn; cấu hình timeout theo từng giai đoạn | Báo cáo dễ tái lập; không còn hướng dẫn full suite mặc định vô tình chạy bảo vệ/reset. |
| P2 | Sau khi ổn định, bổ sung dữ liệu mixed-case/space riêng, thử browser/chế độ hiển thị cần thiết và chính sách hết hạn nếu thuộc phạm vi | Mở rộng coverage có căn cứ; không biến yêu cầu chưa được chốt thành lỗi website. |

## 7. Kế hoạch chạy lại xác nhận thực tế

1. Sao lưu báo cáo bằng thư mục run riêng trước mọi pytest, vì hook hiện tại reset CSV. Ghi phiên bản source/hash, Python/Selenium/Chrome/driver, timezone, headless và tên biến cấu hình có/không; tuyệt đối không xuất giá trị bí mật. Lưu original Bảng 4.8 hoặc biên bản xác nhận expected trước khi đánh giá chính sách.
2. Kiểm tra driver và điều hướng GET bằng môi trường được phép; khảo sát DOM login/reset/account và banner read-only. Đối chiếu selector, chứng minh account link public hay protected; ghi metadata che dữ liệu. Nếu môi trường chặn, ghi BLOCKED/SKIP kèm nguyên nhân, không phỏng đoán website.
3. Chạy tuần tự nhóm ít tác động trước: LOG-11 và LOG-05/06/07; không tăng số lần chạy mù khi timeout. Ghi trạng thái disabled, native validity, ARIA/error đúng trường và challenge. Nếu có CAPTCHA cần thao tác thủ công thì dừng theo quy trình, không tính validation PASS.
4. Chạy LOG-01 đã PASS nguyên trạng làm baseline; xác nhận danh tính theo cách không lưu dữ liệu nhạy cảm. Sau baseline mới chạy LOG-02 và hai nhánh LOG-09, LOG-12/13 từng test độc lập. Với 12/13 ghi rõ đã tới logout/Back/reload/tab hay chưa. Không dùng login thất bại để đánh FAIL chức năng downstream.
5. Chạy LOG-03/04 và các dữ liệu LOG-08 với account/dữ liệu đã xác minh, số lượt được giới hạn và khoảng nghỉ theo chính sách site. Mỗi input có kết quả riêng; theo dõi tổng sai trên account/IP. Nếu bị bảo vệ sớm, ghi hiện tượng và dừng, không retry tự động để vượt chặn.
6. LOG-14: chạy ca trống trước; chỉ gửi một yêu cầu mỗi địa chỉ được kiểm soát khi có phép, xác nhận UI theo chính sách chống dò tài khoản. Nếu expected gồm gửi thư, kiểm tra inbox test một lần và ghi kết quả riêng; không gửi hàng loạt. Tách lỗi mở form khỏi lỗi xử lý recovery.
7. LOG-10 không chạy trong đợt thông thường. Chỉ chạy riêng khi đã xác nhận quyền, tài khoản dùng một lần, cơ chế/cooldown và kế hoạch phục hồi. Đếm request thực nhận qua bằng chứng được phép đã che bí mật; dừng khi bảo vệ xuất hiện; ghi kết quả quan sát theo chính sách, không bypass CAPTCHA.
8. Đối chiếu CSV/HTML/diagnostic cùng run, đủ node bắt buộc và subcase; phân loại mỗi lỗi thành website, automation, dữ liệu/môi trường hoặc chưa đủ bằng chứng. Chỉ xác nhận lỗi website khi tái hiện hành vi sai expected sau thao tác hợp lệ, có bằng chứng nội dung và trạng thái; traceback Selenium đơn lẻ không đáp ứng điều kiện đó.

Lần đánh giá này hoàn tất bằng phân tích tĩnh và artefact hiện có. Các bước chạy lại ở trên là đề xuất, chưa được thực hiện.
