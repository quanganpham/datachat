"""
Vanna AI SQL Agent Configuration (Multi-Dataset)
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
OPENAI_MODEL = "gpt-4o"  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo

# ============================================
# Database Configuration (Multi-Dataset)
# ============================================
VACCINE_DB_PATH = os.path.join(BASE_DIR, "vaccine.db")
LONGCHAU_DB_PATH = os.path.join(BASE_DIR, "longchau.db")

# Legacy support - default database path
DATABASE_PATH = VACCINE_DB_PATH

# Dataset registry
DATASETS = {
    "vaccine": {
        "name": "Tiêm Chủng Long Châu",
        "short_name": "Vaccine",
        "icon": "💉",
        "description": "Dữ liệu tiêm chủng vaccine",
        "db_path": VACCINE_DB_PATH,
        "color": "#01B5B4",
    },
    "longchau": {
        "name": "Nhà Thuốc Long Châu",
        "short_name": "Nhà Thuốc",
        "icon": "💊",
        "description": "Dữ liệu nhà thuốc và dược phẩm",
        "db_path": LONGCHAU_DB_PATH,
        "color": "#2563EB",
    },
}

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
