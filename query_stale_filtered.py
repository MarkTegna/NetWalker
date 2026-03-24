"""Show stale devices after applying marktests/netwalker.ini filters."""
import pyodbc
import base64
from datetime import datetime
from fnmatch import fnmatch

# Filters from marktests/netwalker.ini
EXCLUDE_HOSTNAMES = ["LUM*"]
EXCLUDE_PLATFORMS = [
    "nutanix", "aruba", "ata", "axis", "cisco paging group",
    "cisco ip phone", "poly", "brightsign", "cannon network camera",
    "algo", "pnm", "qnp", "logitech", "screencloud", "pan-os"
]
EXCLUDE_CAPABILITIES = ["camera", "printer"]
SKIP_AFTER_FAILURES = 3

server = "eit-prisqldb01.tgna.tegna.com"
database = "NetWalker"
username = "NetWalker"
password = base64.b64decode("Rmx1ZmZ5QnVubnlIaXRieWFCdXM=").decode()
conn = pyodbc.connect(
    f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};"
    f"UID={username};PWD={password};TrustServerCertificate=yes"
)
cursor = conn.cursor()

days = 2
cursor.execute("""
    SELECT
        d.device_name, d.last_seen, d.platform, d.hardware_model,
        d.capabilities, d.connection_method, d.connection_failures,
        COALESCE(
            (SELECT TOP 1 ip_address FROM device_interfaces
             WHERE device_id = d.device_id
             ORDER BY CASE
                WHEN interface_name LIKE '%Management%' THEN 1
                WHEN interface_name LIKE '%Loopback%' THEN 2
                WHEN interface_name LIKE '%Vlan%' THEN 3 ELSE 4 END,
                interface_name), ''
        ) AS ip_address
    FROM devices d
    WHERE d.status = 'active'
      AND d.hardware_model != 'Unwalked Neighbor'
      AND d.last_seen < DATEADD(day, -?, GETDATE())
    ORDER BY d.last_seen ASC
""", (days,))

rows = cursor.fetchall()
now = datetime.now()

kept = []
filtered_out = []

for r in rows:
    name = r[0]
    platform = r[2] or ''
    caps = r[4] or ''
    failures = r[6]
    reason = None

    # Hostname filter (fnmatch)
    for pat in EXCLUDE_HOSTNAMES:
        if fnmatch(name.lower(), pat.lower()):
            reason = f"hostname matches '{pat}'"
            break

    # Platform filter (substring)
    if not reason and platform:
        for ep in EXCLUDE_PLATFORMS:
            if ep in platform.lower():
                reason = f"platform '{platform}' contains '{ep}'"
                break

    # Capability filter (substring, but skip if has infrastructure caps)
    if not reason and caps:
        cap_list = [c.strip().lower() for c in caps.split(',')]
        infra = {'router', 'switch'}
        has_infra = bool(infra & set(cap_list))
        for ec in EXCLUDE_CAPABILITIES:
            if ec in cap_list and not has_infra:
                reason = f"capability '{ec}' (no infra caps)"
                break

    # Connection failure threshold
    if not reason and failures >= SKIP_AFTER_FAILURES:
        reason = f"connection_failures={failures} >= {SKIP_AFTER_FAILURES}"

    if reason:
        filtered_out.append((r, reason))
    else:
        kept.append(r)

print(f"=== Stale devices with marktests filters applied ===")
print(f"Total stale (>2 days): {len(rows)}")
print(f"Filtered out: {len(filtered_out)}")
print(f"Would actually be walked: {len(kept)}\n")

if kept:
    print(f"{'Device Name':<40} {'Last Seen':<22} {'Days':<6} {'IP':<18} {'Method':<12} {'Fail':<5} {'Platform':<12}")
    print("-" * 115)
    for r in kept:
        last = r[1]
        if last and isinstance(last, str):
            last = datetime.strptime(last[:19], '%Y-%m-%d %H:%M:%S')
        days_ago = (now - last).days if last else '?'
        print(f"{r[0]:<40} {str(r[1])[:19]:<22} {days_ago:<6} {(r[7] or ''):<18} {(r[5] or 'NULL'):<12} {r[6]:<5} {(r[2] or ''):<12}")

if filtered_out:
    print(f"\n--- Filtered Out ({len(filtered_out)}) ---")
    print(f"{'Device Name':<40} {'Reason':<60}")
    print("-" * 100)
    for r, reason in filtered_out:
        print(f"{r[0]:<40} {reason:<60}")

cursor.close()
conn.close()
