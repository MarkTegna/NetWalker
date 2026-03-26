"""
Find and purge orphaned device records - devices with the same serial number
but different device_name, where a newer record exists.

This handles cases like hostname corrections (STUIOD1 -> STUDIO1) that leave
stale records that never get updated.
"""
import pyodbc
import base64
import sys

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()

conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password}"
)
cursor = conn.cursor()

# Find serial numbers that appear on multiple device_name records
# Exclude 'unknown' serials (unwalked neighbors)
cursor.execute("""
    SELECT serial_number, COUNT(DISTINCT device_name) as name_count
    FROM devices
    WHERE serial_number != 'unknown'
      AND status = 'active'
    GROUP BY serial_number
    HAVING COUNT(DISTINCT device_name) > 1
    ORDER BY name_count DESC
""")

dupes = cursor.fetchall()

if not dupes:
    print("No orphaned duplicates found.")
    cursor.close()
    conn.close()
    sys.exit(0)

print(f"Found {len(dupes)} serial numbers with multiple device names:\n")

orphans = []

for serial, count in dupes:
    cursor.execute("""
        SELECT device_id, device_name, serial_number, platform, hardware_model,
               connection_failures, connection_method,
               CONVERT(VARCHAR, last_seen, 120) as last_seen,
               CONVERT(VARCHAR, first_seen, 120) as first_seen
        FROM devices
        WHERE serial_number = ? AND status = 'active'
        ORDER BY last_seen DESC
    """, (serial,))

    rows = cursor.fetchall()
    print(f"Serial: {serial} ({count} records)")
    print("-" * 100)

    # The newest record (first row) is the keeper, rest are orphans
    for i, r in enumerate(rows):
        tag = "  KEEP  " if i == 0 else "  ORPHAN"
        print(f"  {tag} | ID: {r[0]:<6} | Name: {r[1]:<35} | HW: {r[4]:<20} | Last: {r[7]} | Failures: {r[5]} | Method: {r[6] or 'None'}")
        if i > 0:
            orphans.append((r[0], r[1], serial, r[7]))
    print()

if not orphans:
    print("No orphans to clean up.")
    cursor.close()
    conn.close()
    sys.exit(0)

print(f"\n{'=' * 80}")
print(f"Total orphaned records to purge: {len(orphans)}")
print(f"{'=' * 80}\n")

for dev_id, name, serial, last_seen in orphans:
    print(f"  Will DELETE: {name} (ID: {dev_id}, serial: {serial}, last_seen: {last_seen})")

dry_run = "--dry-run" in sys.argv
if dry_run:
    print("\n[DRY RUN] No changes made. Run without --dry-run to purge.")
    cursor.close()
    conn.close()
    sys.exit(0)

print()
confirm = input("Type 'YES' to purge these orphaned records: ")
if confirm != "YES":
    print("Cancelled.")
    cursor.close()
    conn.close()
    sys.exit(0)

deleted = 0
for dev_id, name, serial, last_seen in orphans:
    try:
        # Delete neighbor references first (destination FK is NO ACTION, not CASCADE)
        cursor.execute("DELETE FROM device_neighbors WHERE destination_device_id = ?", (dev_id,))
        dest_refs = cursor.rowcount
        cursor.execute("DELETE FROM device_neighbors WHERE source_device_id = ?", (dev_id,))
        src_refs = cursor.rowcount
        # Now delete the device (CASCADE handles interfaces, versions, vlans, stack_members)
        cursor.execute("DELETE FROM devices WHERE device_id = ?", (dev_id,))
        deleted += cursor.rowcount
        print(f"  [OK] Deleted {name} (ID: {dev_id}) + {dest_refs + src_refs} neighbor refs")
    except pyodbc.Error as e:
        print(f"  [FAIL] Error deleting {name} (ID: {dev_id}): {e}")

conn.commit()
cursor.close()
conn.close()

print(f"\nPurged {deleted} orphaned device records.")
