"""Add connection_method column to devices table."""
import pyodbc
import base64

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()

conn_str = (
    f"DRIVER={{SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"TrustServerCertificate=yes"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sys.columns
                  WHERE object_id = OBJECT_ID('devices')
                  AND name = 'connection_method')
    BEGIN
        ALTER TABLE devices ADD connection_method NVARCHAR(20) NULL;
    END
""")
conn.commit()
print("connection_method column added successfully")

# Verify
cursor.execute("SELECT TOP 1 connection_method FROM devices")
print("Column verified - exists in table")

cursor.close()
conn.close()
