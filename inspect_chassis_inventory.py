"""Inspect ChassisInventory.xls structure"""
import xml.etree.ElementTree as ET

file_path = r"D:\MJODev\NetWalker\prodtest_files\ChassisInventory.xls"

tree = ET.parse(file_path)
root = tree.getroot()

ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}

ws = root.find('.//ss:Worksheet', ns)
table = ws.find('.//ss:Table', ns)
rows = table.findall('.//ss:Row', ns)

print(f"Total rows: {len(rows)}")
print("\nRows 0-10:")

for row_idx in range(min(11, len(rows))):
    row = rows[row_idx]
    cells = row.findall('.//ss:Cell', ns)
    print(f"\nRow {row_idx} ({len(cells)} cells):")
    
    for col_idx in range(min(15, len(cells))):
        cell = cells[col_idx]
        data = cell.find('.//ss:Data', ns)
        value = data.text if data is not None and data.text else "[EMPTY]"
        if value != "[EMPTY]":
            print(f"  Col {col_idx}: {value}")
