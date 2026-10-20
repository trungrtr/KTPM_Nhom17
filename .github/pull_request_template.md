## Nội dung
- Module: (REG / LOG / SRC / ...)
- TC ID liên quan:

## Checklist
- [ ] Đã chạy test của module, ổn định (≥ 3 lần liên tiếp)
- [ ] Locator chỉ nằm trong `pages/`, test không gọi `By.*`
- [ ] Không có `time.sleep` > 2 giây
- [ ] Tên hàm test = TC ID (vd `test_REG_01_register_valid`)
- [ ] Không commit mật khẩu, token, file `.env`
