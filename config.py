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
load_dotenv(dotenv_path=ENV_PATH)

# ============================================
# LLM Configuration (OpenAI)
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ LỖI: Không tìm thấy OPENAI_API_KEY!")
    print("Vui lòng đảm bảo file .env đã được copy sang máy Mac (Mac thường ẩn file bắt đầu bằng dấu chấm).")
    print("Bạn có thể bấm Command + Shift + . để hiện file ẩn trên Mac.")
    sys.exit(1)

OPENAI_MODEL = "gpt-4o"  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo

# ============================================
# Database Configuration
# ============================================
DATABASE_PATH = "./my_data.db"

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
