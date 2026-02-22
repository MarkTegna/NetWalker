"""
List all tables in the NetWalker database
"""
import pyodbc

conn_str = (
    "DRIVER={SQL Server};"
    "SERVER=eit-prisqldb01.tgna.tegna.com;"
    "DATABASE=NetWalker;"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("=== ALL TABLES IN NetWalker DATABASE ===")
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    ORDER BY TABLE_NAME
""")

tables = cursor.fetchall()
print(f"\nFound {len(tables)} tables:")
for table in tables:
    print(f"  - {table[0]}")
    
    # Get row count for each table
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"    ({count:,} rows)")
    except Exception as e:
        print(f"    (Error counting: {e})")

conn.close()
