# 💬 DataChat - Trợ lý Phân tích Dữ liệu

SQL Agent thông minh - hỏi đáp dữ liệu bằng tiếng Việt, có lưu lịch sử hội thoại.

![DataChat UI](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-🚀-green) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple)

## ✨ Tính năng

- 🤖 Hỏi đáp dữ liệu bằng **tiếng Việt tự nhiên**
- 🧠 AI **nhớ ngữ cảnh** cuộc trò chuyện (20 cặp Q&A)
- 💾 Lưu lịch sử hội thoại, chuyển đổi giữa các cuộc chat
- 🛡️ Chặn các lệnh SQL nguy hiểm (DELETE, DROP, INSERT...)
- 🎨 Giao diện dark theme premium

---

## 🚀 Hướng dẫn cài đặt

### 1. Clone repo

```bash
git clone https://github.com/quanganpham/datachat.git
cd datachat
```

### 2. Cài dependencies

```bash
pip install -r requirements.txt
```

### 3. Tạo file `.env`

Tạo file `.env` trong thư mục gốc (copy từ `.env.example`):

```bash
cp .env.example .env
```

Mở file `.env` và điền API key:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
HOST=localhost
PORT=8000
```

> ⚠️ Bạn cần có OpenAI API key. Lấy tại: https://platform.openai.com/api-keys

### 4. Chạy server

```bash
python app.py
```

### 5. Mở trình duyệt

Truy cập: **http://localhost:8000**

---

## 📁 Cấu trúc project

```
datachat/
├── app.py              # FastAPI server
├── sql_agent.py        # Core AI agent (OpenAI GPT-4o)
├── chat_store.py       # Lưu trữ lịch sử hội thoại
├── train_schema.py     # SCHEMA_PROMPT (business rules)
├── config.py           # Configuration
├── csv_to_db.py        # Import CSV vào SQLite
├── explore_db.py       # Khám phá cấu trúc database
├── my_data.db          # SQLite database
├── requirements.txt    # Dependencies
├── .env.example        # Mẫu file environment
├── templates/
│   └── index.html      # Giao diện chat
└── csv_data/           # Dữ liệu CSV gốc
```

## 🔧 Cách cập nhật dữ liệu

1. Đặt file CSV mới vào `csv_data/`
2. Chạy `python csv_to_db.py` để import vào database
3. (Tùy chọn) Chạy `python explore_db.py` để xem cấu trúc
4. Cập nhật business rules trong `train_schema.py` nếu cần
5. Restart server: `python app.py`

## 📝 License

MIT
