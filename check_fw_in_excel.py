import openpyxl

wb = openpyxl.load_workbook('D:/MJODev/NetWalker/marktests/reports/Inventory_20260222-09-14.xlsx')
ws = wb.active

print("Searching for KGW-MAIN-FW01 in inventory...")
print()

for row in ws.iter_rows(min_row=2):
    if row[0].value and 'KGW-MAIN-FW01' in str(row[0].value):
        print(f"Found: {row[0].value}")
        if len(row) > 1:
            print(f"  IP: {row[1].value}")
        if len(row) > 2:
            print(f"  Platform: {row[2].value}")
        if len(row) > 3:
            print(f"  Capabilities: {row[3].value}")
        if len(row) > 4:
            print(f"  Hardware: {row[4].value}")
        if len(row) > 5:
            print(f"  Serial: {row[5].value}")
        if len(row) > 6:
            print(f"  Status: {row[6].value}")
