# NetWalker Web Interface - Installation Checklist

**Author:** Mark Oldham  
**Version:** 1.0.0

## Pre-Installation Requirements

### System Requirements
- [ ] Windows 10/11 or Windows Server 2016+
- [ ] Python 3.8 or higher installed
- [ ] Network access to SQL Server (eit-prisqldb01.tgna.tegna.com)
- [ ] At least 100MB free disk space
- [ ] Modern web browser (Chrome, Edge, Firefox, Safari)

### Software Requirements
- [ ] Python installed and in PATH
- [ ] pip (Python package manager) available
- [ ] ODBC Driver 17 or 18 for SQL Server installed

## Installation Steps

### Step 1: Verify Python Installation
```powershell
python --version
# Should show Python 3.8 or higher
```
- [ ] Python version verified

### Step 2: Check ODBC Driver
```powershell
# Open ODBC Data Source Administrator
odbcad32.exe
# Check "Drivers" tab for "ODBC Driver 17 for SQL Server" or "ODBC Driver 18 for SQL Server"
```
- [ ] ODBC Driver verified

If not installed, download from:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Step 3: Navigate to Application Directory
```powershell
cd netwalker_web
```
- [ ] In correct directory

### Step 4: Install Python Dependencies
```powershell
pip install -r requirements.txt
```
Expected output:
```
Successfully installed Flask-3.0.0 pyodbc-5.0.1 Werkzeug-3.0.1
```
- [ ] Dependencies installed successfully

### Step 5: Verify Installation
```powershell
python -c "import flask; import pyodbc; print('All imports successful')"
```
- [ ] All imports successful

### Step 6: Test Database Connection
```powershell
python -c "import pyodbc; conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=eit-prisqldb01.tgna.tegna.com,1433;DATABASE=NetWalker;UID=NetWalker;PWD=FluffyBunnyHitbyaBus;TrustServerCertificate=yes;'); print('Database connection successful'); conn.close()"
```
- [ ] Database connection successful

### Step 7: Start the Application
```powershell
python app.py
```
Expected output:
```
==================================================
NetWalker Web Interface v1.0.0
Author: Mark Oldham
==================================================

Starting server on http://0.0.0.0:5000
Database: eit-prisqldb01.tgna.tegna.com / NetWalker

Press Ctrl+C to stop the server
```
- [ ] Application started successfully

### Step 8: Test in Browser
1. Open web browser
2. Navigate to: http://localhost:5000
3. Verify dashboard loads with statistics

- [ ] Dashboard loads successfully
- [ ] Statistics display correctly
- [ ] Navigation menu works

## Post-Installation Verification

### Functional Tests
- [ ] Dashboard displays device count
- [ ] Devices page loads and shows devices
- [ ] Click on a device shows detail page
- [ ] VLANs page loads and shows VLANs
- [ ] Click on a VLAN shows detail page
- [ ] Interfaces page loads and shows interfaces
- [ ] Reports page loads
- [ ] Platform distribution report works
- [ ] Software version report works
- [ ] Stale devices report works
- [ ] VLAN consistency report works
- [ ] Global search returns results
- [ ] Filtering works on all pages
- [ ] Breadcrumb navigation works
- [ ] Back button works

### Performance Tests
- [ ] Pages load in under 2 seconds
- [ ] No errors in browser console
- [ ] No errors in application console

## Optional Configuration

### Create Custom Configuration File
```powershell
copy config.ini.template config.ini
notepad config.ini
# Edit settings as needed
```
- [ ] Configuration file created (optional)

### Change Port (if 5000 is in use)
Edit `config.ini`:
```ini
[web]
port = 8080
```
- [ ] Port changed (if needed)

### Set Production Secret Key
Edit `config.ini`:
```ini
[web]
secret_key = your-random-secret-key-here
```
- [ ] Secret key set (for production)

## Troubleshooting

### Issue: Python not found
**Solution:**
1. Install Python from python.org
2. During installation, check "Add Python to PATH"
3. Restart PowerShell

- [ ] Resolved

### Issue: ODBC Driver not found
**Solution:**
1. Download ODBC Driver from Microsoft
2. Install driver
3. Verify in odbcad32.exe

- [ ] Resolved

### Issue: pip not found
**Solution:**
```powershell
python -m ensurepip --upgrade
```

- [ ] Resolved

### Issue: Database connection failed
**Possible causes:**
1. Not on network with access to SQL Server
2. Firewall blocking connection
3. Incorrect credentials
4. SQL Server not running

**Solution:**
1. Verify network connectivity
2. Check firewall settings
3. Verify credentials in app.py
4. Contact database administrator

- [ ] Resolved

### Issue: Port 5000 already in use
**Solution:**
1. Change port in config.ini
2. Or stop other application using port 5000

- [ ] Resolved

### Issue: Module not found errors
**Solution:**
```powershell
pip install --upgrade -r requirements.txt
```

- [ ] Resolved

## Production Deployment Checklist

### Security
- [ ] Change secret key in config.ini
- [ ] Disable debug mode in config.ini
- [ ] Use HTTPS (configure reverse proxy)
- [ ] Implement authentication (if needed)
- [ ] Review database permissions

### Performance
- [ ] Install Waitress: `pip install waitress`
- [ ] Use Waitress instead of Flask dev server
- [ ] Configure connection pooling
- [ ] Enable database query caching
- [ ] Monitor application performance

### Monitoring
- [ ] Set up application logging
- [ ] Monitor database connections
- [ ] Track page load times
- [ ] Set up error alerting

### Backup
- [ ] Document configuration
- [ ] Backup config.ini
- [ ] Document custom changes
- [ ] Create deployment documentation

## Final Verification

### All Systems Go
- [ ] Application starts without errors
- [ ] Database connection works
- [ ] All pages load correctly
- [ ] All features work as expected
- [ ] Performance is acceptable
- [ ] No errors in logs

## Installation Complete!

Congratulations! NetWalker Web Interface is now installed and running.

### Next Steps:
1. Read QUICK_START.md for usage guide
2. Explore the application features
3. Run reports to analyze your network
4. Customize as needed for your environment

### Getting Help:
- Documentation: README.md
- Quick Start: QUICK_START.md
- Architecture: ARCHITECTURE.md
- Project Summary: PROJECT_SUMMARY.md

### Support:
- Author: Mark Oldham
- Repository: https://github.com/MarkTegna/NetWalker

---

**Installation Date:** _________________

**Installed By:** _________________

**Notes:** _________________
