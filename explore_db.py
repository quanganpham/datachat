"""
Database Explorer - Analyze database structure for prompt optimization
"""
import sqlite3

def explore_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    print("=" * 60)
    print("DATABASE ANALYSIS FOR PROMPT OPTIMIZATION")
    print("=" * 60)
    
    for table in tables:
        print(f"\n{'='*60}")
        print(f"TABLE: {table}")
        print("=" * 60)
        
        # Get row count
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"Total rows: {count:,}")
        
        # Get columns and types
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = cursor.fetchall()
        print(f"\nColumns ({len(columns)}):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Sample data
        print(f"\nSample data (3 rows):")
        cursor.execute(f'SELECT * FROM "{table}" LIMIT 3')
        rows = cursor.fetchall()
        col_names = [c[1] for c in columns]
        for row in rows:
            print(f"  {dict(zip(col_names, row))}")
        
        # Distinct values for TEXT columns
        print(f"\nDistinct values (TEXT columns):")
        for col in columns:
            if col[2] == 'TEXT':
                col_name = col[1]
                cursor.execute(f'SELECT DISTINCT "{col_name}" FROM "{table}" WHERE "{col_name}" IS NOT NULL LIMIT 10')
                values = [v[0] for v in cursor.fetchall()]
                if values:
                    print(f"  {col_name}: {values[:5]}{'...' if len(values) > 5 else ''}")
    
    conn.close()

if __name__ == "__main__":
    explore_database("./my_data.db")
