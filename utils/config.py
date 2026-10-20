"""Đọc cấu hình từ file .env (mỗi người tự tạo .env từ .env.example)."""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://www.coolmate.me")
TEST_EMAIL = os.getenv("TEST_EMAIL", "")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DEFAULT_TIMEOUT = 10
