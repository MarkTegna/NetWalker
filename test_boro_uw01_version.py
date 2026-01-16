"""Test to capture show version output from BORO-UW01"""
from scrapli.driver.core import IOSXEDriver
import base64

# Decode password
password = base64.b64decode("dm9nb24jWmFwaG9kNHBpenphJA==").decode('utf-8')

device = {
    "host": "BORO-UW01",
    "auth_username": "ep-moldham",
    "auth_password": password,
    "auth_strict_key": False,
    "transport": "paramiko",
}

try:
    conn = IOSXEDriver(**device)
    conn.open()
    
    result = conn.send_command("show version")
    print("=" * 80)
    print("SHOW VERSION OUTPUT:")
    print("=" * 80)
    print(result.result)
    print("=" * 80)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
