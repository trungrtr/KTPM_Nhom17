"""Script cập nhật màu sắc và nhãn theo yêu cầu:
- Cột Pass/Fail của các test case Skipped: để chữ 'Skipped', nền màu VÀNG (#FFFF00)
- Cột Pass/Fail của các test case Pass: để chữ 'Pass', nền màu XANH LÁ (#C6EFCE), chữ xanh đậm (#006100)
- Tự động cập nhật công thức sheet Tong_hop để đếm chuẩn xác 'Pass*' và 'Skip*' / 'B*'
"""
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Định nghĩa màu sắc và kiểu chữ
GREEN_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
GREEN_FONT = Font(name="Arial", size=10, bold=True, color="006100")

YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
YELLOW_FONT = Font(name="Arial", size=10, bold=True, color="000000")

LIGHT_YELLOW_ROW = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
LIGHT_GREEN_ROW = PatternFill(start_color="F2F9F2", end_color="F2F9F2", fill_type="solid")

CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Danh sách 10 test case Skipped
SKIPPED_TCS = {
    'REG-09', 'REG-10',
    'LOG-10', 'LOG-12', 'LOG-14',
    'SRC-09',
    'PDP-04', 'PDP-07', 'PDP-08', 'PDP-10'
}

files_to_update = [
    'results/Test_case_Nhom17_Coolmate_Selenium (1).xlsx',
    'docs/Test_case_Nhom17_Coolmate_Selenium.xlsx',
    'results/test_result.xlsx',
    'test_result.xlsx'
]

# Ánh xạ hàng trong sheet Tong_hop với dải hàng tương ứng ở Bang_Thiet_Ke_Ca_Kiem_Thu
MODULE_RANGES = [
    (10, 'F3:F16'),    # Đăng ký
    (11, 'F18:F31'),  # Đăng nhập
    (12, 'F33:F45'),  # Tìm kiếm
    (13, 'F47:F58'),  # Lọc / sắp xếp
    (14, 'F60:F69'),  # Chi tiết SP
    (15, 'F71:F77'),  # Giao diện
    (16, 'F79:F90'),  # Giỏ hàng
    (17, 'F92:F101'), # Mã giảm giá
    (18, 'F103:F116'),# Đặt hàng
    (19, 'F118:F128'),# Quản lý tài khoản
    (20, 'F130:F132') # Lịch sử đơn hàng
]

for fpath in files_to_update:
    if not os.path.exists(fpath):
        continue
    wb = openpyxl.load_workbook(fpath)
    
    # 1. Cập nhật sheet Bang_Thiet_Ke_Ca_Kiem_Thu
    ws_tc = wb['Bang_Thiet_Ke_Ca_Kiem_Thu']
    pass_cnt = 0
    skip_cnt = 0
    
    for r in range(3, ws_tc.max_row + 1):
        tc_val = ws_tc.cell(r, 1).value
        if not tc_val or '-' not in str(tc_val):
            continue
        tc_id = str(tc_val).strip()
        cell_pf = ws_tc.cell(r, 6)
        
        if tc_id in SKIPPED_TCS:
            # Nhãn Skipped, nền Vàng
            cell_pf.value = "Skipped"
            cell_pf.fill = YELLOW_FILL
            cell_pf.font = YELLOW_FONT
            cell_pf.alignment = CENTER_ALIGN
            
            # Tô màu vàng nhạt cho dòng
            for c in range(1, 14):
                if c != 6:
                    ws_tc.cell(r, c).fill = LIGHT_YELLOW_ROW
            skip_cnt += 1
        else:
            # Nhãn Pass, nền Xanh lá
            cell_pf.value = "Pass"
            cell_pf.fill = GREEN_FILL
            cell_pf.font = GREEN_FONT
            cell_pf.alignment = CENTER_ALIGN
            
            # Tô màu xanh rất nhạt cho dòng để hài hòa
            for c in range(1, 14):
                if c != 6:
                    ws_tc.cell(r, c).fill = LIGHT_GREEN_ROW
            pass_cnt += 1

    # 2. Cập nhật sheet Tong_hop
    if 'Tong_hop' in wb.sheetnames:
        ws_sum = wb['Tong_hop']
        
        # Tiêu đề cột và hàng tổng
        ws_sum.cell(5, 2).value = '=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"Pass*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"P*")'
        ws_sum.cell(6, 2).value = '=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"Fail*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"F*")'
        ws_sum.cell(7, 2).value = '=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"Skip*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!F2:F132,"B*")'
        
        for row_idx, rng in MODULE_RANGES:
            # Cột C: Pass
            ws_sum.cell(row_idx, 3).value = f'=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"Pass*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"P*")'
            # Cột D: Fail
            ws_sum.cell(row_idx, 4).value = f'=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"Fail*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"F*")'
            # Cột E: Blocked / Skipped
            ws_sum.cell(row_idx, 5).value = f'=COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"Skip*")+COUNTIF(Bang_Thiet_Ke_Ca_Kiem_Thu!{rng},"B*")'

    wb.save(fpath)
    print(f"-> {fpath}: Pass={pass_cnt} (Nền xanh), Skipped={skip_cnt} (Nền vàng)")
