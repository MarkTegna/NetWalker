# NetWalker Web UI - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Access to NetWalker SQL Server database
- NetWalker configuration file (`netwalker.ini`)

## Installation

### Option 1: Using Startup Script (Recommended)

**Windows PowerShell:**
```powershell
cd netwalker_web
.\start.ps1
```

**Windows Command Prompt:**
```cmd
cd netwalker_web
start.bat
```

The startup script will:
1. Check Python installation
2. Create virtual environment (if needed)
3. Install dependencies
4. Start the web server

### Option 2: Manual Installation

1. **Create virtual environment:**
   ```powershell
   python -m venv venv
   ```

2. **Activate virtual environment:**
   ```powershell
   # PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Command Prompt
   venv\Scripts\activate.bat
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```powershell
   python app.py
   ```

## Access the Application

Once started, open your browser and navigate to:

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Configuration

The application uses `netwalker.ini` for database configuration. This file should already be copied from the NetWalker project.

If you need to modify settings, edit `netwalker.ini`:

```ini
[database]
enabled = true
server = your-sql-server.domain.com
port = 1433
database = NetWalker
username = NetWalker
password = ENC:base64encodedpassword
trust_server_certificate = true
```

## Features

### Dashboard
- View summary statistics (device count, stacks, connections, VLANs)
- Search devices by name, IP, or serial number
- Browse recent devices
- View platform distribution chart

### API Endpoints

**Devices:**
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `GET /api/devices/search/{query}` - Search devices

**Topology:**
- `GET /api/topology` - Get full network topology
- `GET /api/topology/{device_id}` - Get device neighbors

**Stack Members:**
- `GET /api/stacks` - List all stack devices
- `GET /api/stacks/{device_id}/members` - Get stack members

**Reports:**
- `GET /api/reports/devices` - Generate device inventory Excel report
- `GET /api/reports/stacks` - Generate stack members Excel report

**Statistics:**
- `GET /api/stats/summary` - Get summary statistics
- `GET /api/stats/platforms` - Get platform statistics

## Troubleshooting

### Database Connection Failed

**Error:** `Failed to connect to database`

**Solution:**
1. Verify `netwalker.ini` exists in the `netwalker_web` directory
2. Check database server is accessible
3. Verify credentials are correct
4. Test connection from NetWalker first

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
1. Stop any other application using port 8000
2. Or change the port in `config.py`:
   ```python
   PORT = 8080  # Change to different port
   ```

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
1. Ensure virtual environment is activated
2. Run: `pip install -r requirements.txt`

### Permission Denied (Excel Reports)

**Error:** `Permission denied` when generating reports

**Solution:**
1. Ensure `reports/` directory exists and is writable
2. Close any open Excel files with the same name

## Development

### Running in Debug Mode

Edit `config.py`:
```python
DEBUG = True
```

Then restart the application. The server will auto-reload on code changes.

### Adding New API Endpoints

1. Create new file in `backend/api/`
2. Define router and endpoints
3. Import and include router in `app.py`

### Customizing Frontend

- HTML files: `frontend/*.html`
- CSS: `frontend/static/css/style.css`
- JavaScript: `frontend/static/js/*.js`

## Production Deployment

### Using Waitress (Windows)

```powershell
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

### Using Windows Service (NSSM)

```powershell
# Install NSSM
# Download from: https://nssm.cc/download

# Install service
nssm install NetWalkerWeb "C:\Python\python.exe" "C:\NetWalker\netwalker_web\app.py"
nssm set NetWalkerWeb AppDirectory "C:\NetWalker\netwalker_web"
nssm start NetWalkerWeb
```

### Using Docker

```powershell
# Build image
docker build -t netwalker-web .

# Run container
docker run -d -p 8000:8000 --name netwalker-web netwalker-web
```

## Support

For issues or questions:
- Check `DATABASE_SCHEMA.md` for database structure
- Review API documentation at `/docs`
- Check NetWalker main project documentation

## Version

Current Version: 0.1.0  
Author: Mark Oldham  
License: MIT (same as NetWalker)
