# NetWalker Web Interface

**Version:** 1.0.0  
**Author:** Mark Oldham  
**Platform:** Windows

## Overview

NetWalker Web Interface is a Flask-based web application that provides a comprehensive front-end for querying and exploring the NetWalker inventory database. It offers intuitive navigation, filtering, and detailed views of all network devices, VLANs, and interfaces.

## Features

### Dashboard
- Real-time statistics (active devices, VLANs, interfaces, platforms)
- Recently updated devices
- Quick navigation links

### Device Management
- List all devices with filtering by platform, status, and search
- Detailed device view with:
  - Device information (name, serial, platform, hardware model)
  - Software version history
  - All interfaces with IP addresses
  - All VLANs configured on the device
- Clickable rows for easy navigation

### VLAN Management
- List all VLANs with filtering by name and number
- Detailed VLAN view with:
  - VLAN information (number, name, timestamps)
  - All devices using this VLAN
  - Port counts per device
- Clickable rows for easy navigation

### Interface Management
- List all interfaces with filtering by type and search
- Detailed interface view with:
  - Interface information (name, IP, subnet, type)
  - Parent device link
  - Timestamps
- Search by interface name, IP address, or device name

### Reports
- **Platform Distribution**: Device count by platform type
- **Software Version Distribution**: Current software versions across all devices
- **Stale Devices**: Devices not seen recently (configurable threshold)
- **VLAN Consistency**: VLANs with inconsistent names across devices

### Global Search
- Search across devices, VLANs, and interfaces
- Results grouped by category
- Clickable results for quick navigation

### Navigation
- Breadcrumb navigation on all pages
- Back button functionality
- Persistent search bar in navigation
- Active page highlighting

## Installation

### Prerequisites

1. **Python 3.8+** installed
2. **ODBC Driver 17 or 18 for SQL Server** installed
3. **Access to NetWalker database** (eit-prisqldb01.tgna.tegna.com)

### Install ODBC Driver (if not already installed)

Download and install from Microsoft:
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Install Python Dependencies

```powershell
cd netwalker_web
pip install -r requirements.txt
```

## Configuration

The application is pre-configured to connect to the NetWalker database. If you need to change the connection settings, edit `app.py`:

```python
DB_CONFIG = {
    'server': 'eit-prisqldb01.tgna.tegna.com',
    'port': 1433,
    'database': 'NetWalker',
    'username': 'NetWalker',
    'password': 'FluffyBunnyHitbyaBus',
    'driver': 'ODBC Driver 17 for SQL Server'
}
```

## Running the Application

### Development Mode

```powershell
cd netwalker_web
python app.py
```

The application will start on `http://localhost:5000`

### Production Mode

For production deployment, use a WSGI server like Waitress:

```powershell
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## Usage

### Accessing the Application

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. Use the navigation menu to explore different sections

### Filtering and Search

- **Devices Page**: Filter by platform, status, or search by name/serial
- **VLANs Page**: Filter by VLAN number or search by name
- **Interfaces Page**: Filter by type or search by interface/IP/device
- **Global Search**: Use the search bar in the navigation to search across all categories

### Viewing Details

- Click on any row in a table to view detailed information
- Use the "Back" link or browser back button to return to the previous page
- Use breadcrumb navigation to jump to any parent page

### Reports

1. Click "Reports" in the navigation menu
2. Select a report to view
3. Some reports have configurable parameters (e.g., stale devices threshold)

## Database Schema

The application queries the following tables:

- **devices**: Network devices (routers, switches, etc.)
- **device_versions**: Software versions per device
- **device_interfaces**: Interfaces and IP addresses
- **vlans**: Master VLAN registry
- **device_vlans**: VLAN-to-device associations

For complete database documentation, see `.kiro/steering/netwalker-database.md`

## File Structure

```
netwalker_web/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── templates/                      # HTML templates
    ├── base.html                   # Base template with navigation
    ├── index.html                  # Dashboard
    ├── devices.html                # Device list
    ├── device_detail.html          # Device details
    ├── vlans.html                  # VLAN list
    ├── vlan_detail.html            # VLAN details
    ├── interfaces.html             # Interface list
    ├── interface_detail.html       # Interface details
    ├── reports.html                # Reports menu
    ├── report_platforms.html       # Platform distribution report
    ├── report_software.html        # Software version report
    ├── report_stale.html           # Stale devices report
    ├── report_vlan_consistency.html # VLAN consistency report
    └── search.html                 # Global search results
```

## Troubleshooting

### Connection Errors

If you see "Database error: Connection failed":

1. Verify ODBC driver is installed: `odbcad32.exe`
2. Test database connectivity from command line
3. Check firewall settings
4. Verify credentials in `app.py`

### ODBC Driver Not Found

If you see "Data source name not found":

1. Install ODBC Driver 17 or 18 for SQL Server
2. Update `DB_CONFIG['driver']` in `app.py` to match your installed driver
3. Check available drivers: Run `odbcad32.exe` and view "Drivers" tab

### Port Already in Use

If port 5000 is already in use:

```python
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=8080)
```

### Slow Performance

For large datasets:

1. Ensure database indexes are created (see database setup documentation)
2. Use filtering options to reduce result sets
3. Consider adding pagination for large tables

## Security Considerations

### Production Deployment

For production use:

1. **Change the secret key** in `app.py`:
   ```python
   app.secret_key = 'your-secure-random-key-here'
   ```

2. **Disable debug mode**:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

3. **Use environment variables** for credentials:
   ```python
   import os
   DB_CONFIG['password'] = os.getenv('NETWALKER_DB_PASSWORD')
   ```

4. **Use HTTPS** with a reverse proxy (nginx, IIS)

5. **Implement authentication** if exposing to untrusted networks

## Future Enhancements

Potential features for future versions:

- User authentication and authorization
- Export to CSV/Excel functionality
- Advanced filtering with multiple criteria
- Graphical charts and visualizations
- Device comparison tool
- Change history tracking
- Email alerts for stale devices
- API endpoints for programmatic access
- Pagination for large result sets
- Saved searches and bookmarks

## Support

For questions or issues:
- Contact: Mark Oldham
- Repository: https://github.com/MarkTegna/NetWalker

## License

See LICENSE file in the NetWalker repository.

## Version History

- **v1.0.0 (2026-01-19)**: Initial release
  - Complete web interface for NetWalker database
  - Device, VLAN, and interface management
  - Comprehensive reporting
  - Global search functionality
  - Responsive design with modern UI
