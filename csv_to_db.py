"""
CSV to SQLite Database Converter (Multi-Dataset)
==================================================
Import CSV files from multiple dataset folders into separate SQLite databases.

Cách sử dụng:
    1. Đặt CSV vào csv_data/vaccin/ và csv_data/LC_data/
    2. Chạy: python csv_to_db.py
    3. Sẽ tạo ra vaccine.db và longchau.db

Lưu ý:
    - Tên file CSV sẽ trở thành tên bảng
    - Dòng đầu tiên của CSV phải là tên các cột
    - Tự động phát hiện encoding
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

# ============================================
# Cấu hình (Configuration)
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_BASE = os.path.join(BASE_DIR, "csv_data")

# Cấu hình cho từng dataset
DATASETS = {
    "vaccine": {
        "csv_folder": os.path.join(CSV_BASE, "vaccin"),
        "db_path": os.path.join(BASE_DIR, "vaccine.db"),
        "table_name_fix": lambda name: name.replace("V2_1dim_", "V2_dim_"),
    },
    "longchau": {
        "csv_folder": os.path.join(CSV_BASE, "LC_data"),
        "db_path": os.path.join(BASE_DIR, "longchau.db"),
        "table_name_fix": lambda name: name,  # Giữ nguyên
    },
}

# Danh sách các encoding sẽ thử (theo thứ tự ưu tiên)
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
            # Strip whitespace/newlines from column names (fix hidden chars from CSV)
            df.columns = [col.strip() for col in df.columns]
            return df, encoding
        except UnicodeDecodeError as e:
            errors.append(f"{encoding}: {e}")
            continue
        except Exception as e:
            # Lỗi khác (không phải encoding) thì raise luôn
            raise e
    
    # Không encoding nào hoạt động
    raise ValueError(f"Không thể đọc file với các encoding: {encodings}\nChi tiết: {errors}")


def csv_to_sqlite(csv_folder: str, db_path: str, table_name_fix=None, encodings: list = None):
    """
    Đọc tất cả file CSV trong thư mục và nhập vào SQLite database.
    Tự động phát hiện encoding của từng file.
    
    Args:
        csv_folder: Đường dẫn thư mục chứa các file CSV
        db_path: Đường dẫn file database output
        table_name_fix: Hàm tùy chỉnh tên bảng (optional)
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
    
    print(f"📁 Thư mục CSV: {csv_folder.absolute()}")
    print(f"💾 Database output: {Path(db_path).absolute()}")
    print(f"📄 Tìm thấy {len(csv_files)} file CSV")
    print()
    
    # Xóa database cũ nếu tồn tại
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Đã xóa database cũ: {os.path.basename(db_path)}")
    
    # Kết nối database
    conn = sqlite3.connect(db_path)
    
    success_count = 0
    
    for csv_file in csv_files:
        table_name = csv_file.stem  # Lấy tên file (không có .csv)
        
        # Áp dụng fix tên bảng nếu có
        if table_name_fix:
            table_name = table_name_fix(table_name)
        
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
    
    print(f"✅ HOÀN TẤT: {success_count}/{len(csv_files)} bảng được tạo → {os.path.basename(db_path)}")
    print()
    
    return True


def verify_database(db_path: str):
    """Kiểm tra TẤT CẢ các bảng trong database có truy vấn được không."""
    if not os.path.exists(db_path):
        print(f"❌ Database không tồn tại: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Lấy danh sách bảng
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    db_name = os.path.basename(db_path)
    print(f"\n🔍 KIỂM TRA DATABASE: {db_name}")
    print("─" * 50)
    
    all_ok = True
    for (table_name,) in tables:
        try:
            # Test SELECT
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = cursor.fetchone()[0]
            
            # Test lấy cột
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = cursor.fetchall()
            col_names = [c[1] for c in columns]
            
            # Test truy vấn thực tế
            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 1')
            sample = cursor.fetchone()
            
            status = "✅" if row_count > 0 else "⚠️ TRỐNG"
            print(f"  {status} {table_name}: {row_count:,} dòng, {len(col_names)} cột")
            
        except Exception as e:
            print(f"  ❌ {table_name}: LỖI - {e}")
            all_ok = False
    
    conn.close()
    
    if all_ok:
        print(f"\n✅ Tất cả {len(tables)} bảng trong {db_name} hoạt động tốt!")
    else:
        print(f"\n⚠️ Có bảng bị lỗi trong {db_name}!")
    
    return all_ok


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
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        row_count = cursor.fetchone()[0]
        
        # Lấy thông tin cột
        cursor.execute(f'PRAGMA table_info("{table_name}")')
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
    print("=" * 60)
    print("📊 CSV TO SQLITE CONVERTER (Multi-Dataset)")
    print("=" * 60)
    print()
    
    for dataset_key, cfg in DATASETS.items():
        print(f"\n{'━' * 60}")
        print(f"📦 DATASET: {dataset_key.upper()}")
        print(f"{'━' * 60}")
        
        csv_to_sqlite(
            cfg["csv_folder"],
            cfg["db_path"],
            table_name_fix=cfg.get("table_name_fix"),
        )
    
    # Kiểm tra tất cả databases
    print(f"\n{'═' * 60}")
    print("🔍 KIỂM TRA KẾT NỐI TẤT CẢ CÁC BẢNG")
    print(f"{'═' * 60}")
    
    for dataset_key, cfg in DATASETS.items():
        verify_database(cfg["db_path"])
    
    print("\n✅ HOÀN TẤT! Các database đã sẵn sàng.")
