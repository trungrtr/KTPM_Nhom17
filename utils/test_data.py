"""Đọc dữ liệu từ data/*.csv cho @pytest.mark.parametrize (data-driven)."""
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def read_csv(filename):
    """Trả về list[dict]; mỗi dòng CSV là một bộ dữ liệu kiểm thử."""
    with open(DATA_DIR / filename, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
