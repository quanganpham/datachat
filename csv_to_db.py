"""
CSV to SQLite Database Converter
=================================
Script để nhập các file CSV vào một file SQLite database (.db)

Cách sử dụng:
    1. Đặt các file CSV vào thư mục "csv_data" (hoặc sửa CSV_FOLDER bên dưới)
    2. Chạy: python csv_to_db.py
    3. File database sẽ được tạo tại OUTPUT_DB_PATH

Lưu ý:
    - Tên file CSV sẽ trở thành tên bảng (ví dụ: nhan_vien.csv -> bảng "nhan_vien")
    - Dòng đầu tiên của CSV phải là tên các cột
    - Tự động phát hiện encoding (UTF-8, Windows-1252, Windows-1258, Latin-1)
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# ============================================
# Cấu hình (Configuration)
# ============================================

# Thư mục chứa các file CSV
CSV_FOLDER = "./csv_data"

# Đường dẫn file database output
OUTPUT_DB_PATH = "./my_data.db"

# Danh sách các encoding sẽ thử (theo thứ tự ưu tiên)
# - utf-8-sig: UTF-8 với BOM (thường từ Excel "Save as UTF-8 CSV")
# - utf-8: UTF-8 chuẩn
# - cp1252: Windows Western European (rất phổ biến khi export từ Excel)
# - cp1258: Windows Vietnamese (encoding tiếng Việt cũ)
# - latin-1: ISO-8859-1 (đọc được mọi byte, dùng làm fallback)
ENCODINGS_TO_TRY = ["utf-8-sig", "utf-8", "cp1252", "cp1258", "latin-1"]


# ============================================
# Hàm chính
# ============================================

def read_csv_auto_encoding(csv_path: Path, encodings: list) -> tuple[pd.DataFrame, str]:
    """
    Đọc file CSV bằng cách thử nhiều encoding cho đến khi thành công.
    
    Args:
        csv_path: Đường dẫn file CSV
        encodings: Danh sách các encoding để thử
        
    Returns:
        Tuple (DataFrame, encoding đã dùng)
        
    Raises:
        ValueError: Nếu không encoding nào hoạt động
    """
    errors = []
    
    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            return df, encoding
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {e}")
            continue
        except Exception as e:
            # Lỗi khác (không phải encoding) thì raise luôn
            raise e
    
    # Không encoding nào hoạt động
    raise ValueError(f"Không thể đọc file với các encoding: {encodings}\nChi tiết: {errors}")


def csv_to_sqlite(csv_folder: str, db_path: str, encodings: list = None):
    """
    Đọc tất cả file CSV trong thư mục và nhập vào SQLite database.
    Tự động phát hiện encoding của từng file.
    
    Args:
        csv_folder: Đường dẫn thư mục chứa các file CSV
        db_path: Đường dẫn file database output
        encodings: Danh sách encoding để thử (mặc định dùng ENCODINGS_TO_TRY)
    """
    if encodings is None:
        encodings = ENCODINGS_TO_TRY
        
    csv_folder = Path(csv_folder)
    
    # Kiểm tra thư mục tồn tại
    if not csv_folder.exists():
        print(f"❌ Lỗi: Thư mục '{csv_folder}' không tồn tại!")
        print(f"   Hãy tạo thư mục và đặt các file CSV vào đó.")
        return False
    
    # Tìm tất cả file CSV
    csv_files = list(csv_folder.glob("*.csv"))
    
    if not csv_files:
        print(f"❌ Lỗi: Không tìm thấy file CSV nào trong '{csv_folder}'")
        return False
    
    print("=" * 60)
    print("📊 CSV TO SQLITE CONVERTER")
    print("=" * 60)
    print(f"📁 Thư mục CSV: {csv_folder.absolute()}")
    print(f"💾 Database output: {Path(db_path).absolute()}")
    print(f"📄 Tìm thấy {len(csv_files)} file CSV")
    print(f"🔤 Encodings sẽ thử: {', '.join(encodings)}")
    print()
    
    # Xóa database cũ nếu tồn tại
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Đã xóa database cũ: {db_path}")
    
    # Kết nối database
    conn = sqlite3.connect(db_path)
    
    success_count = 0
    
    for csv_file in csv_files:
        table_name = csv_file.stem  # Lấy tên file (không có .csv)
        
        try:
            # Đọc CSV với auto-detect encoding
            print(f"📥 Đang xử lý: {csv_file.name}")
            df, detected_encoding = read_csv_auto_encoding(csv_file, encodings)
            
            # Hiển thị thông tin
            print(f"   ├─ Encoding: {detected_encoding}")
            print(f"   ├─ Số dòng: {len(df):,}")
            print(f"   ├─ Số cột: {len(df.columns)}")
            print(f"   └─ Các cột: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
            
            # Ghi vào SQLite
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            print(f"   ✅ Đã tạo bảng '{table_name}'")
            print()
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Lỗi: {e}")
            print()
    
    conn.close()
    
    print("=" * 60)
    print(f"✅ HOÀN TẤT: {success_count}/{len(csv_files)} bảng được tạo")
    print(f"💾 Database: {Path(db_path).absolute()}")
    print("=" * 60)
    print()
    print("📝 Bước tiếp theo:")
    print(f"   1. Mở file config.py")
    print(f"   2. Sửa DATABASE_PATH = \"{db_path}\"")
    print(f"   3. Cập nhật SCHEMA_PROMPT trong train_schema.py (hoặc chạy train_schema.py để xem schema)")
    print(f"   4. Chạy: python main.py")
    
    return True


def show_db_info(db_path: str):
    """Hiển thị thông tin các bảng trong database."""
    if not os.path.exists(db_path):
        print(f"❌ Database không tồn tại: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lấy danh sách bảng
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print()
    print("=" * 60)
    print(f"📊 THÔNG TIN DATABASE: {db_path}")
    print("=" * 60)
    
    for (table_name,) in tables:
        # Đếm số dòng
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        # Lấy thông tin cột
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n📋 Bảng: {table_name}")
        print(f"   Số dòng: {row_count:,}")
        print(f"   Các cột:")
        for col in columns:
            col_id, col_name, col_type, not_null, default, pk = col
            pk_marker = " 🔑" if pk else ""
            print(f"      - {col_name} ({col_type}){pk_marker}")
    
    conn.close()
    print()


if __name__ == "__main__":
    # Chạy chuyển đổi (tự động phát hiện encoding)
    csv_to_sqlite(CSV_FOLDER, OUTPUT_DB_PATH)
    
    # Hiển thị thông tin database đã tạo
    show_db_info(OUTPUT_DB_PATH)
