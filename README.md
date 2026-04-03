# 💬 DataChat — Trợ lý Phân tích Dữ liệu bằng AI

**SQL Agent thông minh — Hỏi đáp dữ liệu bằng tiếng Việt cho Hệ thống FPT Long Châu.**

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-🚀-green) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-purple) ![SQLite](https://img.shields.io/badge/SQLite-💾-orange) ![Version](https://img.shields.io/badge/Version-3.0-teal)

---

## 1. MỤC TIÊU

Thay vì chờ đội Data/IT viết báo cáo (mất hàng giờ/ngày), người dùng chỉ cần **gõ câu hỏi bằng tiếng Việt** và nhận kết quả trong **dưới 10 giây**:

```mermaid
flowchart LR
    A["👤 Quản lý\ngõ câu hỏi\ntiếng Việt"] -->|"Vài giây"| B["🤖 DataChat\nAI tự dịch & truy vấn"]
    B -->|"Trả kết quả\nngay lập tức"| A
    
    style A fill:#D1FAE5,stroke:#10B981,color:#000
    style B fill:#DBEAFE,stroke:#3B82F6,color:#000
```

### Khả năng cốt lõi

| Khả năng | Mô tả | Ví dụ |
|----------|--------|-------|
| **Truy vấn tức thì** | Biến câu hỏi tiếng Việt thành báo cáo số liệu | *"Top 5 vaccine bán chạy nhất?"* |
| **Hiểu ngữ cảnh** | Trả lời câu hỏi nối tiếp dựa trên lịch sử | *"Giải thích cách tính kết quả trên"* |
| **Đa bộ dữ liệu** | Chuyển đổi nhanh giữa các phân hệ kinh doanh | 💉 Vaccine ↔ 💊 Nhà thuốc |
| **Chống bịa số** | Từ chối trả lời khi không có dữ liệu, thay vì đoán | Cơ chế Anti-Hallucination |

---

## 2. KIẾN TRÚC TỔNG THỂ

```mermaid
flowchart TB
    subgraph CLIENT["🖥️ GIAO DIỆN NGƯỜI DÙNG (Trình duyệt Web)"]
        direction LR
        UI_CHAT["💬 Khung trò chuyện"]
        UI_SWITCH["🔀 Nút chuyển Dataset"]
        UI_TABLE["📊 Bảng kết quả"]
        UI_SQL["📝 Hiển thị SQL"]
        UI_HISTORY["📋 Lịch sử hội thoại"]
    end

    subgraph SERVER["⚙️ MÁY CHỦ XỬ LÝ (Backend API - Python FastAPI)"]
        direction TB
        ROUTER["🚦 Bộ định tuyến\n(nhận câu hỏi, chọn đúng dataset)"]
        AGENT_V["🤖 AI Agent\nVaccine"]
        AGENT_LC["🤖 AI Agent\nNhà Thuốc"]
        STORE["💾 Bộ nhớ hội thoại\n(Chat Store)"]
    end

    subgraph AI["🧠 LÕI TRÍ TUỆ NHÂN TẠO"]
        direction TB
        GPT["OpenAI GPT-4o"]
        PROMPT_V["📘 Bản đồ dữ liệu\nVaccine\n(13 bảng, 800+ dòng hướng dẫn)"]
        PROMPT_LC["📗 Bản đồ dữ liệu\nNhà Thuốc\n(11 bảng, 360+ dòng hướng dẫn)"]
    end

    subgraph DATA["🗄️ CƠ SỞ DỮ LIỆU"]
        direction LR
        DB_V["vaccine.db\n13 bảng · 2.9 MB"]
        DB_LC["longchau.db\n11 bảng · 2.5 MB"]
        DB_CHAT["chat_history.db\nLịch sử trò chuyện"]
    end

    CLIENT <-->|"① Người dùng gửi câu hỏi\n② Nhận lại báo cáo + bảng số liệu"| SERVER
    ROUTER -->|"Nếu dataset = Vaccine"| AGENT_V
    ROUTER -->|"Nếu dataset = Nhà Thuốc"| AGENT_LC
    ROUTER <-->|"③ Lưu/đọc lịch sử\nhội thoại trước đó"| STORE
    AGENT_V <-->|"④ Gửi câu hỏi + bản đồ dữ liệu\n⑤ Nhận lại câu lệnh SQL"| GPT
    AGENT_LC <-->|"④ Gửi câu hỏi + bản đồ dữ liệu\n⑤ Nhận lại câu lệnh SQL"| GPT
    GPT -.-|"AI đọc bản đồ\nđể hiểu cấu trúc bảng"| PROMPT_V
    GPT -.-|"AI đọc bản đồ\nđể hiểu cấu trúc bảng"| PROMPT_LC
    AGENT_V <-->|"⑥ Chạy SQL vào database\n⑦ Nhận bảng kết quả thô"| DB_V
    AGENT_LC <-->|"⑥ Chạy SQL vào database\n⑦ Nhận bảng kết quả thô"| DB_LC
    STORE <-->|"Lưu mỗi câu hỏi\nvà câu trả lời"| DB_CHAT

    style CLIENT fill:#F0FDF4,stroke:#16A34A,color:#000
    style SERVER fill:#EFF6FF,stroke:#2563EB,color:#000
    style AI fill:#FFF7ED,stroke:#EA580C,color:#000
    style DATA fill:#F5F3FF,stroke:#7C3AED,color:#000
```

| Đường | Từ → Đến | Dữ liệu truyền tải |
|-------|----------|---------------------|
| **①** | Giao diện → Máy chủ | Câu hỏi tiếng Việt + loại dataset đang chọn |
| **②** | Máy chủ → Giao diện | Bài phân tích AI + câu lệnh SQL + bảng số liệu |
| **③** | Bộ định tuyến ↔ Chat Store | Đọc 20 cặp hỏi-đáp gần nhất + Lưu tin nhắn mới |
| **④** | AI Agent → GPT-4o | Câu hỏi + Bản đồ dữ liệu (~800 dòng) + Lịch sử |
| **⑤** | GPT-4o → AI Agent | Câu lệnh SQL + Giải thích ngắn |
| **⑥** | AI Agent → Database | Câu lệnh SQL (đã qua kiểm duyệt an ninh) |
| **⑦** | Database → AI Agent | Bảng kết quả thô |

---

## 3. LUỒNG XỬ LÝ (5 bước mỗi câu hỏi)

```mermaid
sequenceDiagram
    actor User as 👤 Người dùng
    participant UI as 🖥️ Giao diện Web
    participant API as ⚙️ Máy chủ API
    participant AI as 🧠 AI (GPT-4o)
    participant DB as 🗄️ Cơ sở dữ liệu

    Note over User,DB: ── BƯỚC 1: TIẾP NHẬN & ĐỊNH TUYẾN ──
    User->>UI: Gõ "Top 5 vaccine bán chạy nhất?"
    UI->>API: Gửi câu hỏi + loại dataset (Vaccine)
    API->>API: Chọn AI Agent phù hợp (Vaccine Agent)

    Note over User,DB: ── BƯỚC 2: DỊCH THUẬT (Tiếng Việt → SQL) ──
    API->>AI: Gửi: câu hỏi + bản đồ dữ liệu + lịch sử
    AI-->>API: Trả về: câu lệnh SQL + giải thích

    Note over User,DB: ── BƯỚC 3: KIỂM DUYỆT AN NINH ──
    API->>API: ✅ Chỉ cho phép SELECT, chặn DELETE/DROP/INSERT

    Note over User,DB: ── BƯỚC 4: TRUY XUẤT DỮ LIỆU ──
    API->>DB: Chạy câu lệnh SQL đã kiểm duyệt
    DB-->>API: Trả về bảng số liệu thô

    Note over User,DB: ── BƯỚC 5: DIỄN GIẢI & TRẢ KẾT QUẢ ──
    API->>AI: Gửi: câu hỏi + số liệu thô
    AI-->>API: Trả về: Báo cáo tiếng Việt có cấu trúc
    API-->>UI: Trả JSON (câu trả lời + SQL + bảng dữ liệu)
    UI-->>User: Hiển thị báo cáo hoàn chỉnh
```

---

## 4. DỮ LIỆU

### Vaccine (13 bảng)

| Loại | Bảng | Nội dung |
|------|------|----------|
| 📊 Giao dịch | `vaccine_sales_order_detail` | Chi tiết đơn bán hàng tiêm chủng |
| 📊 Giao dịch | `vaccine_returned_order_detail` | Chi tiết đơn hoàn trả |
| 📊 Giao dịch | `vaccine_record` | Hồ sơ tiêm chủng |
| 📁 Danh mục | `dim_product` | Danh sách sản phẩm vaccine (170 loại) |
| 📁 Danh mục | `dim_shop` | Thông tin trung tâm tiêm chủng |
| 📁 Danh mục | `dim_person` | Thông tin khách hàng (đã mã hóa PII) |
| 📁 Danh mục | `dim_person_address` / `dim_family_member` | Địa chỉ & gia đình |
| 📁 Danh mục | `dim_vaccine_disease_group` | Nhóm bệnh (60 nhóm) |
| 📁 Danh mục | `dim_vaccine_regimen` | Phác đồ tiêm chủng |
| 📁 Danh mục | `dim_statellite_shop` | Shop vệ tinh (Vaccine ↔ Nhà thuốc) |

### Nhà Thuốc Long Châu (11 bảng)

| Loại | Bảng | Nội dung |
|------|------|----------|
| 📊 Giao dịch | `fact_order_detail_oms_flc` | Chi tiết đơn hàng nhà thuốc |
| 📁 Sản phẩm | `dim_product_sku_pim_flc` | SKU sản phẩm (mã, tên, ngành hàng) |
| 📁 Sản phẩm | `dim_products_cms_flc` | Chi tiết CMS (thành phần, liều dùng) |
| 📁 Sản phẩm | `dim_product_measures_pim_flc` | Đơn vị đo lường |
| 📁 Sản phẩm | `dim_product_taxonomies_pim_flc` | Phân loại bệnh/nhóm SP |
| 📁 Danh mục | `dim_categories_cms_flc` / `dim_category_pim_flc` | Danh mục sản phẩm (CMS + PIM) |

### Sơ đồ liên kết — Vaccine

```mermaid
flowchart LR
    SALES["📊 Đơn bán"] -->|sku = item_code| PRODUCT["📦 Sản phẩm"]
    SALES -->|shop_code = code| SHOP["🏥 Trung tâm"]
    SALES -->|customer_id| PERSON["👤 Khách hàng"]
    SALES -->|sku| DISEASE["🦠 Nhóm bệnh"]
    RETURNED["📊 Đơn hoàn trả"] -->|sku| PRODUCT
    RETURNED -->|shop_code = code| SHOP
    RECORD["📊 Hồ sơ tiêm"] -->|sku| PRODUCT
    RECORD -->|shop_code = code| SHOP

    style SALES fill:#DBEAFE,stroke:#2563EB,color:#000
    style RETURNED fill:#FEE2E2,stroke:#EF4444,color:#000
    style RECORD fill:#D1FAE5,stroke:#10B981,color:#000
    style PRODUCT fill:#FEF3C7,stroke:#F59E0B,color:#000
```

### Sơ đồ liên kết — Nhà thuốc

```mermaid
flowchart LR
    ORDERS["📊 Đơn hàng"] -->|"CAST(item_code) = CAST(code)"| SKU["📦 SKU"]
    SKU -->|product_id = sku_id| MEASURES["📏 Đơn vị đo"]
    SKU -->|product_id = sku_id| TAXONOMY["🏷️ Phân loại"]
    SKU -->|product_id| CAT_LINK["🔗 Liên kết"]
    CAT_LINK -->|category_id = id| CAT_PIM["📂 Danh mục PIM"]
    CMS["📝 Sản phẩm CMS"] -->|category = id| CAT_CMS["📂 Danh mục CMS"]

    style ORDERS fill:#DBEAFE,stroke:#2563EB,color:#000
    style SKU fill:#FEF3C7,stroke:#F59E0B,color:#000
    style CMS fill:#E0E7FF,stroke:#6366F1,color:#000
```

---

## 5. BẢO MẬT 3 LỚP

```mermaid
flowchart TB
    subgraph L1["🛡️ LỚP 1: Bảo vệ API Key"]
        direction LR
        ENV["Khóa API lưu trong .env\n(không đưa lên Git)"]
    end
    
    subgraph L2["🛡️ LỚP 2: Kiểm duyệt SQL"]
        direction LR
        CHECK1["✅ Chỉ cho phép\nSELECT / WITH"]
        CHECK2["❌ Chặn: DELETE\nDROP, INSERT\nUPDATE, ALTER"]
        CHECK3["❌ Quét SQL Injection"]
    end
    
    subgraph L3["🛡️ LỚP 3: Chống ảo giác (Anti-Hallucination)"]
        direction LR
        ANTI1["0 dòng kết quả?\n→ Ép AI nói 'không có dữ liệu'"]
        ANTI2["Có dữ liệu?\n→ Ép AI CHỈ dùng số thật"]
    end

    L1 --> L2 --> L3

    style L1 fill:#FEF3C7,stroke:#D97706,color:#000
    style L2 fill:#FEE2E2,stroke:#DC2626,color:#000
    style L3 fill:#D1FAE5,stroke:#059669,color:#000
```

---

## 6. CẤU TRÚC PROJECT

```
datachat/
├── app.py                 # FastAPI server + định tuyến API
├── sql_agent.py           # Lõi AI Agent (Text→SQL→Answer)
├── chat_store.py          # Lưu trữ lịch sử hội thoại
├── config.py              # Cấu hình (API key, DB paths, datasets)
├── train_schema.py        # 📘 Bản đồ dữ liệu Vaccine (800+ dòng)
├── train_schema_lc.py     # 📗 Bản đồ dữ liệu Nhà Thuốc (365 dòng)
├── csv_to_db.py           # Công cụ nhập CSV → SQLite
├── vaccine.db             # 🗄️ DB Vaccine (13 bảng)
├── longchau.db            # 🗄️ DB Nhà Thuốc (11 bảng)
├── chat_history.db        # 💾 Lịch sử hội thoại
├── requirements.txt       # Dependencies
├── .env                   # 🔑 API Key (KHÔNG push lên Git)
├── templates/
│   └── index.html         # 🖥️ Giao diện web (HTML+CSS+JS)
├── static/                # Logo, hình ảnh
└── csv_data/
    ├── vaccin/            # 13 tệp CSV dữ liệu Vaccine
    └── LC_data/           # 11 tệp CSV dữ liệu Nhà Thuốc
```

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

```bash
cp .env.example .env
```

Mở `.env` và điền API key:

```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
HOST=localhost
PORT=8000
```

> ⚠️ Cần OpenAI API key. Lấy tại: https://platform.openai.com/api-keys

### 4. Import dữ liệu (nếu cần)

```bash
python csv_to_db.py
```

### 5. Chạy server

```bash
python app.py
```

Truy cập: **http://localhost:8000**

---

## 🔧 Cập nhật dữ liệu

1. Đặt file CSV vào `csv_data/vaccin/` hoặc `csv_data/LC_data/`
2. Chạy `python csv_to_db.py` để import vào database
3. Cập nhật Schema Prompt (`train_schema.py` / `train_schema_lc.py`) nếu có cột/bảng mới
4. Restart server: `python app.py`

---

## 🆘 Troubleshooting

| Lỗi | Giải pháp |
|-----|-----------|
| Conflict khi `git pull` ở file `.db` | `git checkout HEAD -- chat_history.db` rồi `git pull` |
| "Không tìm thấy OPENAI_API_KEY" | Đảm bảo file `.env` tồn tại và có key. Trên Mac, file `.` là file ẩn (`Cmd+Shift+.`) |
| "Không tìm thấy database" | Chạy `python csv_to_db.py` để tạo DB từ CSV |

---

## 📝 License

MIT
