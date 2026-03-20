import sqlite3
import os
import pandas as pd

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my_data.db")
conn = sqlite3.connect(db_path)

out = open("_join_results.txt", "w", encoding="utf-8")

def test_query(title, query):
    out.write(f"\n=== {title} ===\n")
    try:
        df = pd.read_sql_query(query, conn)
        out.write(f"Rows returned: {len(df)}\n")
        if len(df) > 0:
            out.write(df.head(3).to_string() + "\n")
        else:
            out.write("NO DATA (0 rows)\n")
    except Exception as e:
        out.write(f"Error: {e}\n")

# 1. Check F1 to D4 (Sku = product_unit_id)
test_query(
    "F1 to D4 (sku = product_unit_id)",
    '''
    SELECT o.sku as f1_sku, p.product_unit_id, o.line_item_name, p.product_name 
    FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" o
    JOIN "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_product" p ON o.sku = p.product_unit_id
    LIMIT 5
    '''
)

test_query(
    "F1 sku vs D4 product_id",
    '''
    SELECT o.sku as f1_sku, p.product_id, o.line_item_name, p.product_name 
    FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" o
    JOIN "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_product" p ON o.sku = p.product_id
    LIMIT 5
    '''
)

test_query(
    "F1 sku vs D4 item_code",
    '''
    SELECT o.sku as f1_sku, p.item_code, o.line_item_name, p.product_name 
    FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" o
    JOIN "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_product" p ON o.sku = p.item_code
    LIMIT 5
    '''
)

test_query(
    "F1 to D5 (sku = sku)",
    '''
    SELECT o.sku as f1_sku, dg.sku, o.line_item_name, dg.disease_group_name 
    FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" o
    JOIN "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_vaccine_disease_group" dg ON o.sku = dg.sku
    LIMIT 5
    '''
)

out.write("\n=== SAMPLE DATA ===\n")
c = conn.cursor()
c.execute('SELECT sku, line_item_name FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" LIMIT 3')
out.write(f"F1 sales sku samples: {c.fetchall()}\n")

c.execute('SELECT product_unit_id, product_id, item_code, product_name FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_product" LIMIT 3')
out.write(f"D4 product samples: {c.fetchall()}\n")

c.execute('SELECT sku, vaccine_name, disease_group_name FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_vaccine_disease_group" LIMIT 3')
out.write(f"D5 disease samples: {c.fetchall()}\n")

try:
    c.execute('SELECT TYPEOF(sku) FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_vaccine_sales_order_detail" LIMIT 1')
    out.write(f"F1 sku type: {c.fetchone()[0]}\n")
    
    c.execute('SELECT TYPEOF(product_unit_id) FROM "[CADS-DD] Dữ liệu mẫu Vaccine V2_dim_product" LIMIT 1')
    out.write(f"D4 product_unit_id type: {c.fetchone()[0]}\n")
except Exception as e:
    out.write(f"Type check error: {e}\n")

conn.close()
out.close()
print("DONE")
