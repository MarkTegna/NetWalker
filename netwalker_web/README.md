# NetWalker Web UI

A web-based reporting and visualization interface for NetWalker network discovery data.

## Overview

NetWalker Web UI provides a modern web interface for viewing, searching, and reporting on network device inventory collected by NetWalker. It connects to the same SQL Server database used by NetWalker and provides:

- **Device Inventory**: Browse and search all discovered devices
- **Topology Visualization**: View network connections and relationships
- **Stack Members**: Detailed view of switch stack configurations
- **Reports**: Generate Excel reports from database
- **Search**: Advanced filtering and search capabilities
- **Historical Data**: View device changes over time

## Architecture

- **Backend**: FastAPI (Python) - RESTful API
- **Frontend**: HTML/JavaScript with Bootstrap - Simple, no build process
- **Database**: Microsoft SQL Server (shared with NetWalker)
- **Deployment**: Standalone Python application or Docker container

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Access to NetWalker SQL Server database
- NetWalker configuration file (`netwalker.ini`)

### Installation

1. **Install dependencies**:
   ```powershell
   cd netwalker_web
   pip install -r requirements.txt
   ```

2. **Configure database connection**:
   - Copy `netwalker.ini` from NetWalker project to this directory
   - Or set environment variables:
     ```powershell
     $env:DB_SERVER="your-sql-server.domain.com"
     $env:DB_DATABASE="NetWalker"
     $env:DB_USERNAME="NetWalker"
     $env:DB_PASSWORD="your-password"
     ```

3. **Run the application**:
   ```powershell
   python app.py
   ```

4. **Open browser**:
   - Navigate to: http://localhost:8000
   - API documentation: http://localhost:8000/docs

## Features

### Device Inventory
- View all discovered devices with details
- Filter by platform, status, site
- Search by hostname, IP address, serial number
- Export to Excel

### Topology View
- Visual network topology diagram
- Device connections via CDP/LLDP
- Interactive graph navigation
- Export topology data

### Stack Members
- Detailed switch stack information
- Individual member details
- Serial numbers and models
- Role and state information

### Reports
- Generate Excel reports on-demand
- Device inventory reports
- Stack member reports
- Custom filtered reports
- Historical data exports

### Search & Filter
- Advanced search across all fields
- Multiple filter criteria
- Save favorite searches
- Quick filters for common queries

## API Endpoints

### Devices
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `GET /api/devices/search?q={query}` - Search devices
- `GET /api/devices/filter?platform={platform}&status={status}` - Filter devices

### Topology
- `GET /api/topology` - Get full network topology
- `GET /api/topology/{device_id}` - Get device neighbors
- `GET /api/topology/site/{site_code}` - Get site topology

### Stack Members
- `GET /api/stacks` - List all stack devices
- `GET /api/stacks/{device_id}/members` - Get stack members

### Reports
- `GET /api/reports/devices` - Generate device inventory report
- `GET /api/reports/stacks` - Generate stack member report
- `GET /api/reports/topology` - Generate topology report

### Statistics
- `GET /api/stats/summary` - Database summary statistics
- `GET /api/stats/platforms` - Device count by platform
- `GET /api/stats/sites` - Device count by site

## Configuration

### Database Configuration (`netwalker.ini`)

```ini
[database]
enabled = true
server = your-sql-server.domain.com
port = 1433
database = NetWalker
username = NetWalker
password = ENC:base64encodedpassword
trust_server_certificate = true
connection_timeout = 30
command_timeout = 60
```

### Application Configuration (`config.py`)

```python
# Server settings
HOST = "0.0.0.0"
PORT = 8000
DEBUG = False

# CORS settings (for API access from other domains)
CORS_ORIGINS = ["*"]

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000
```

## Development

### Project Structure

```
netwalker_web/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── DATABASE_SCHEMA.md     # Database schema documentation
│
├── backend/               # Backend API
│   ├── __init__.py
│   ├── database.py        # Database connection and queries
│   ├── models.py          # Data models
│   ├── api/               # API endpoints
│   │   ├── __init__.py
│   │   ├── devices.py     # Device endpoints
│   │   ├── topology.py    # Topology endpoints
│   │   ├── stacks.py      # Stack member endpoints
│   │   ├── reports.py     # Report generation endpoints
│   │   └── stats.py       # Statistics endpoints
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── config_manager.py  # Config file parser (from NetWalker)
│       └── excel_export.py    # Excel generation
│
├── frontend/              # Frontend web interface
│   ├── index.html         # Main page
│   ├── devices.html       # Device inventory page
│   ├── topology.html      # Topology visualization page
│   ├── stacks.html        # Stack members page
│   ├── reports.html       # Reports page
│   ├── static/            # Static assets
│   │   ├── css/
│   │   │   └── style.css  # Custom styles
│   │   └── js/
│   │       ├── api.js     # API client
│   │       ├── devices.js # Device page logic
│   │       ├── topology.js # Topology page logic
│   │       └── common.js  # Shared utilities
│   └── templates/         # HTML templates (if using Jinja2)
│
└── tests/                 # Unit tests
    ├── __init__.py
    ├── test_api.py
    └── test_database.py
```

### Running Tests

```powershell
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Building for Production

```powershell
# Install production dependencies
pip install gunicorn

# Run with Gunicorn (Linux/Mac)
gunicorn app:app --bind 0.0.0.0:8000 --workers 4

# Run with Waitress (Windows)
pip install waitress
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

## Deployment

### Option 1: Standalone Python Application

```powershell
# Install as Windows service using NSSM
nssm install NetWalkerWeb "C:\Python\python.exe" "C:\NetWalker\netwalker_web\app.py"
nssm start NetWalkerWeb
```

### Option 2: Docker Container

```powershell
# Build Docker image
docker build -t netwalker-web .

# Run container
docker run -d -p 8000:8000 --name netwalker-web netwalker-web
```

### Option 3: IIS with FastCGI

1. Install Python and dependencies
2. Configure IIS with FastCGI module
3. Create web.config for FastAPI application
4. Deploy to IIS website

## Security Considerations

### Authentication
- Currently no authentication (internal use only)
- For production, add authentication middleware
- Consider Windows Authentication for corporate environments

### Database Access
- Use read-only database user for web UI
- Limit permissions to SELECT only
- No write operations from web UI

### Network Security
- Deploy behind corporate firewall
- Use HTTPS in production
- Configure CORS appropriately

## Troubleshooting

### Database Connection Issues
```
Error: Cannot connect to database
```
**Solution**: Verify `netwalker.ini` configuration and SQL Server connectivity

### Port Already in Use
```
Error: Address already in use
```
**Solution**: Change PORT in `config.py` or stop conflicting service

### Excel Export Fails
```
Error: Permission denied
```
**Solution**: Ensure write permissions to temp directory

## Future Enhancements

- User authentication and authorization
- Real-time updates via WebSockets
- Advanced topology visualization (D3.js, Cytoscape.js)
- Custom dashboard widgets
- Scheduled report generation
- Email notifications
- Device configuration backup integration
- Change tracking and auditing
- Multi-tenant support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Same license as NetWalker (MIT)

## Author

**Mark Oldham**
- GitHub: [@MarkTegna](https://github.com/MarkTegna)

## Version History

### v0.1.0 (Initial Release)
- Basic device inventory API
- Simple web interface
- Excel report generation
- Database integration

---

**Note**: This is a companion project to NetWalker. NetWalker performs network discovery and populates the database. This web UI provides read-only access for reporting and visualization.
