"""
Vanna AI SQL Agent Configuration
"""
import os
import sys
from dotenv import load_dotenv

# Define base directory explicitly to avoid path issues on Mac/Linux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Load environment variables explicitly from the .env file
if os.path.exists(ENV_PATH):
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print(f"⚠️ CẢNH BÁO: Không tìm thấy file {ENV_PATH}")
    print("Vui lòng copy file .env.example thành .env và điền API Key.")

# ============================================
# LLM Configuration (OpenAI)
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ LỖI: Không tìm thấy OPENAI_API_KEY!")
    print("-" * 50)
    print("HƯỚNG DẪN XỬ LÝ:")
    print("1. Kiểm tra xem bạn đã có file '.env' chưa (file ẩn trên Mac/Linux).")
    print("2. Nếu chưa, hãy chạy lệnh: cp .env.example .env")
    print("3. Mở file .env và dán key vào: OPENAI_API_KEY=sk-xxxxxx")
    print("-" * 50)
    sys.exit(1)

OPENAI_MODEL = "gpt-4o"  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo

# ============================================
# Database Configuration
# ============================================
DATABASE_PATH = os.path.join(BASE_DIR, "my_data.db")

# ============================================
# Server Configuration
# ============================================
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", 8000))

# ============================================
# Agent Memory Configuration
# ============================================
AGENT_MEMORY_MAX_ITEMS = 1000

# ============================================
# User Roles
# ============================================
ADMIN_EMAILS = ["admin@example.com"]
DEFAULT_USER_EMAIL = "user@example.com"
