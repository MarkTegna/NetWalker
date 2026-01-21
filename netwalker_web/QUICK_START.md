# NetWalker Web Interface - Quick Start Guide

**Author:** Mark Oldham  
**Version:** 1.0.0

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

Open PowerShell in the `netwalker_web` directory:

```powershell
pip install -r requirements.txt
```

### Step 2: Start the Application

**Option A - Using Batch File:**
```cmd
start_web.bat
```

**Option B - Using PowerShell:**
```powershell
.\start_web.ps1
```

**Option C - Direct Python:**
```powershell
python app.py
```

### Step 3: Open Your Browser

Navigate to: **http://localhost:5000**

That's it! You're ready to explore your NetWalker database.

---

## What You Can Do

### 1. Dashboard (Home Page)
- View statistics: device count, VLAN count, interfaces, platforms
- See recently updated devices
- Quick navigation to all sections

### 2. Browse Devices
- Click "Devices" in the navigation
- Filter by platform (IOS, IOS-XE, NX-OS, etc.)
- Search by device name or serial number
- Click any device row to see full details

### 3. View Device Details
- Software version history
- All interfaces with IP addresses
- All VLANs configured on the device
- Click "Back" to return to device list

### 4. Browse VLANs
- Click "VLANs" in the navigation
- Filter by VLAN number or search by name
- See device count and total ports per VLAN
- Click any VLAN row to see which devices use it

### 5. Browse Interfaces
- Click "Interfaces" in the navigation
- Filter by interface type (physical, loopback, vlan, tunnel)
- Search by interface name, IP address, or device name
- Click any interface row to see details

### 6. Run Reports
- Click "Reports" in the navigation
- Choose from:
  - **Platform Distribution**: See device count by platform
  - **Software Versions**: See version distribution
  - **Stale Devices**: Find devices not seen recently
  - **VLAN Consistency**: Find VLANs with inconsistent names

### 7. Global Search
- Use the search box in the top navigation bar
- Search across devices, VLANs, and interfaces
- Results are grouped by category
- Click any result to view details

---

## Navigation Tips

### Breadcrumbs
Every page shows breadcrumb navigation at the top:
```
Home / Devices / CORE-SW01
```
Click any breadcrumb to jump to that page.

### Back Button
Every detail page has a "← Back" link to return to the previous list.

### Clickable Rows
All table rows are clickable - just click anywhere on the row to view details.

### Active Page Highlighting
The current page is highlighted in the navigation menu.

---

## Common Queries

### Find a Specific Device
1. Click "Devices"
2. Type device name in search box
3. Click "Filter"
4. Click the device row to view details

### Find All Devices with a VLAN
1. Click "VLANs"
2. Enter VLAN number or search by name
3. Click "Filter"
4. Click the VLAN row
5. See all devices using this VLAN

### Find Which Device Has an IP Address
1. Use the global search box (top navigation)
2. Type the IP address
3. Results show the interface and device

### Check Software Version Compliance
1. Click "Reports"
2. Click "Software Versions"
3. See distribution of all versions
4. Identify devices running non-standard versions

### Find Stale Devices
1. Click "Reports"
2. Click "Stale Devices"
3. Adjust days threshold if needed
4. See devices not seen recently

### Check VLAN Naming Consistency
1. Click "Reports"
2. Click "VLAN Consistency"
3. See VLANs with different names across devices

---

## Keyboard Shortcuts

- **Browser Back Button**: Go back to previous page
- **Ctrl+F**: Search within current page
- **F5**: Refresh current page

---

## Troubleshooting

### Can't Connect to Database
**Error:** "Database error: Connection failed"

**Solutions:**
1. Verify you're on the network with access to `eit-prisqldb01.tgna.tegna.com`
2. Check ODBC Driver is installed (run `odbcad32.exe`)
3. Verify credentials in `app.py`

### Port 5000 Already in Use
**Error:** "Address already in use"

**Solution:** Edit `app.py` and change the port:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```
Then access at `http://localhost:8080`

### Slow Performance
**Issue:** Pages load slowly

**Solutions:**
1. Use filters to reduce result sets
2. Check database indexes are created
3. Close other applications using network/database

### ODBC Driver Not Found
**Error:** "Data source name not found"

**Solution:** Install ODBC Driver 17 or 18 for SQL Server from:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

---

## Next Steps

### Explore the Data
- Browse through devices to understand your network inventory
- Check VLAN distribution across devices
- Review software version compliance
- Identify stale devices that may need attention

### Run Regular Reports
- Weekly: Check stale devices report
- Monthly: Review software version distribution
- As needed: VLAN consistency check

### Customize
- Edit `app.py` to add custom queries
- Modify templates to change appearance
- Add new reports for specific needs

---

## Getting Help

### Documentation
- Full documentation: `README.md`
- Database schema: `.kiro/steering/netwalker-database.md`

### Support
- Contact: Mark Oldham
- Repository: https://github.com/MarkTegna/NetWalker

---

**Enjoy exploring your network with NetWalker Web Interface!**
