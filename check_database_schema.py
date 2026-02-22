"""
Check the actual database schema
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

# Get column names from Devices table
print("=== DEVICES TABLE COLUMNS ===")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Devices'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"  {row.COLUMN_NAME}: {row.DATA_TYPE}")

# Get recent device records
print("\n=== RECENT DEVICES ===")
cursor.execute("SELECT TOP 5 * FROM Devices ORDER BY device_id DESC")
columns = [column[0] for column in cursor.description]
print(f"Columns: {', '.join(columns)}")
for row in cursor.fetchall():
    print(f"  device_id {row[0]}: {row[1]}")

# Check Neighbors table
print("\n=== NEIGHBORS TABLE COLUMNS ===")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'Neighbors'
    ORDER BY ORDINAL_POSITION
""")
for row in cursor.fetchall():
    print(f"  {row.COLUMN_NAME}: {row.DATA_TYPE}")

# Count neighbors for device 482
print("\n=== NEIGHBORS FOR DEVICE 482 ===")
cursor.execute("SELECT COUNT(*) FROM Neighbors WHERE device_id = 482")
count = cursor.fetchone()[0]
print(f"Total neighbors: {count}")

if count > 0:
    cursor.execute("SELECT TOP 10 * FROM Neighbors WHERE device_id = 482")
    columns = [column[0] for column in cursor.description]
    print(f"\nSample neighbors:")
    for row in cursor.fetchall():
        print(f"  {row}")

conn.close()
