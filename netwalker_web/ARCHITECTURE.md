# NetWalker Web Interface - Architecture

**Author:** Mark Oldham  
**Version:** 1.0.0

## Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Browser                          │
│  (Chrome, Edge, Firefox, Safari)                           │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Flask Web Server                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  app.py (Main Application)                           │  │
│  │  - Route handlers                                     │  │
│  │  - Database queries                                   │  │
│  │  - Template rendering                                 │  │
│  │  - Error handling                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Templates (Jinja2)                                   │  │
│  │  - base.html (navigation, layout)                    │  │
│  │  - Page templates (14 files)                         │  │
│  │  - CSS styling (embedded)                            │  │
│  │  - JavaScript (minimal)                              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ pyodbc
                     │ SQL Queries
┌────────────────────▼────────────────────────────────────────┐
│              SQL Server Database                            │
│  Server: eit-prisqldb01.tgna.tegna.com                     │
│  Database: NetWalker                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tables:                                              │  │
│  │  - devices (network devices)                         │  │
│  │  - device_versions (software versions)               │  │
│  │  - device_interfaces (interfaces & IPs)              │  │
│  │  - vlans (VLAN registry)                             │  │
│  │  - device_vlans (device-VLAN associations)           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Request Flow

```
User Action (Click/Search)
    │
    ▼
Browser sends HTTP GET/POST
    │
    ▼
Flask receives request
    │
    ▼
Route handler processes request
    │
    ├─► Parse query parameters (filters, search)
    │
    ├─► Connect to database (pyodbc)
    │
    ├─► Execute SQL query
    │
    ├─► Fetch results
    │
    ├─► Close database connection
    │
    ├─► Render template with data
    │
    ▼
Flask returns HTML response
    │
    ▼
Browser displays page
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                       │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Routes    │  │  Database   │  │  Templates  │       │
│  │             │  │  Manager    │  │             │       │
│  │ @app.route  │──│ get_conn()  │──│  Jinja2     │       │
│  │             │  │ execute()   │  │  render     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│         │                │                  │              │
│         └────────────────┴──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Page Hierarchy

```
NetWalker Web Interface
│
├── Dashboard (/)
│   ├── Statistics Cards
│   ├── Recent Devices Table
│   └── Quick Links
│
├── Devices (/devices)
│   ├── Filter Bar (platform, status, search)
│   ├── Device Table (clickable rows)
│   └── Device Detail (/device/<id>)
│       ├── Device Info Card
│       ├── Software Versions Table
│       ├── Interfaces Table
│       └── VLANs Table
│
├── VLANs (/vlans)
│   ├── Filter Bar (number, name)
│   ├── VLAN Table (clickable rows)
│   └── VLAN Detail (/vlan/<id>)
│       ├── VLAN Info Card
│       └── Devices Table
│
├── Interfaces (/interfaces)
│   ├── Filter Bar (type, search)
│   ├── Interface Table (clickable rows)
│   └── Interface Detail (/interface/<id>)
│       └── Interface Info Card
│
├── Reports (/reports)
│   ├── Platform Distribution (/reports/platforms)
│   ├── Software Versions (/reports/software)
│   ├── Stale Devices (/reports/stale)
│   └── VLAN Consistency (/reports/vlan_consistency)
│
└── Search (/search)
    ├── Device Results
    ├── VLAN Results
    └── Interface Results
```

## Database Query Patterns

### Pattern 1: List with Filtering
```python
# Build dynamic query based on filters
query = "SELECT ... FROM table WHERE 1=1"
params = []

if filter1:
    query += " AND column1 = ?"
    params.append(filter1)

if search:
    query += " AND column2 LIKE ?"
    params.append(f'%{search}%')

cursor.execute(query, params)
results = cursor.fetchall()
```

### Pattern 2: Detail with Related Data
```python
# Get main entity
cursor.execute("SELECT ... FROM table WHERE id = ?", (id,))
entity = cursor.fetchone()

# Get related data
cursor.execute("SELECT ... FROM related WHERE parent_id = ?", (id,))
related = cursor.fetchall()

# Render with both datasets
render_template('detail.html', entity=entity, related=related)
```

### Pattern 3: Aggregation Report
```python
# Group and count
cursor.execute("""
    SELECT column, COUNT(*) as count
    FROM table
    GROUP BY column
    ORDER BY count DESC
""")
results = cursor.fetchall()
```

## Template Inheritance

```
base.html (Master Template)
├── Navigation Bar
├── Breadcrumbs
├── Flash Messages
├── Content Block {% block content %}
└── Footer

    ├── index.html (extends base.html)
    ├── devices.html (extends base.html)
    ├── device_detail.html (extends base.html)
    ├── vlans.html (extends base.html)
    ├── vlan_detail.html (extends base.html)
    ├── interfaces.html (extends base.html)
    ├── interface_detail.html (extends base.html)
    ├── reports.html (extends base.html)
    ├── report_*.html (extends base.html)
    └── search.html (extends base.html)
```

## CSS Architecture

```
base.html <style> section
├── Reset & Base Styles
├── Layout Components
│   ├── Navbar
│   ├── Container
│   ├── Breadcrumb
│   └── Footer
├── UI Components
│   ├── Cards
│   ├── Tables
│   ├── Buttons
│   ├── Forms
│   ├── Badges
│   └── Alerts
└── Utility Classes
    ├── Stats Grid
    ├── Detail Grid
    ├── Filter Bar
    └── Empty State
```

## JavaScript Functionality

```javascript
// Minimal vanilla JavaScript

1. Clickable Table Rows
   - Add click handler to tr.clickable
   - Navigate to data-href attribute

2. Back Button
   - goBack() function
   - Uses window.history.back()

3. Form Submission
   - Standard HTML form submission
   - No AJAX required
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Input Validation                                  │
│  - Query parameter validation                               │
│  - Type checking (int, string)                              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Layer 2: SQL Injection Protection                          │
│  - Parameterized queries (? placeholders)                   │
│  - No string concatenation in SQL                           │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Layer 3: Session Security                                  │
│  - Secret key for session encryption                        │
│  - Secure cookie settings                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Layer 4: Database Connection Security                      │
│  - TrustServerCertificate option                            │
│  - Connection timeout                                       │
│  - Proper connection cleanup                                │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Try:
    Connect to database
    Execute query
    Fetch results
    Render template
    
Except DatabaseError:
    Log error
    Flash error message
    Render template with empty data
    
Finally:
    Close cursor
    Close connection
```

## Configuration Management

```
Startup
    │
    ▼
Check for config.ini
    │
    ├─► Found: Load settings from file
    │   ├─► Database config
    │   ├─► Web server config
    │   └─► Secret key
    │
    └─► Not Found: Use defaults
        ├─► Hardcoded database settings
        ├─► Default web server settings
        └─► Random secret key
```

## Deployment Options

### Option 1: Development (Built-in Flask Server)
```
python app.py
├─► Flask development server
├─► Debug mode enabled
├─► Auto-reload on code changes
└─► Single-threaded
```

### Option 2: Production (Waitress WSGI Server)
```
waitress-serve app:app
├─► Production-ready WSGI server
├─► Multi-threaded
├─► Better performance
└─► No debug mode
```

### Option 3: IIS (Windows Server)
```
IIS + wfastcgi
├─► Windows native deployment
├─► IIS management
├─► Windows authentication support
└─► SSL/TLS support
```

## Performance Optimization

```
Database Level:
├─► Indexes on frequently queried columns
├─► TOP clauses to limit results
├─► Efficient JOINs
└─► Connection pooling

Application Level:
├─► Minimal template logic
├─► Efficient query construction
├─► Proper connection cleanup
└─► Error handling without retries

Frontend Level:
├─► Minimal JavaScript
├─► Embedded CSS (no external files)
├─► Browser caching
└─► Responsive design
```

## Monitoring & Logging

```
Application Logs:
├─► Flask debug output (development)
├─► Error messages to console
├─► Database connection errors
└─► Query execution errors

Database Logs:
├─► SQL Server query logs
├─► Connection logs
└─► Performance metrics

User Activity:
├─► Page views (via Flask)
├─► Search queries
└─► Filter usage
```

## Scalability Considerations

### Current Architecture (Single Server)
```
Web Server (Flask)
    │
    └─► Database (SQL Server)
```

### Future Scalability (Load Balanced)
```
Load Balancer
    │
    ├─► Web Server 1 (Flask)
    ├─► Web Server 2 (Flask)
    └─► Web Server 3 (Flask)
            │
            └─► Database (SQL Server)
                    │
                    └─► Read Replicas
```

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend                                                   │
│  - HTML5                                                    │
│  - CSS3 (embedded)                                          │
│  - JavaScript (vanilla, minimal)                            │
│  - Jinja2 Templates                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Backend                                                    │
│  - Python 3.8+                                              │
│  - Flask 3.0.0                                              │
│  - pyodbc 5.0.1                                             │
│  - Werkzeug 3.0.1                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Database                                                   │
│  - Microsoft SQL Server                                     │
│  - ODBC Driver 17/18                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Platform                                                   │
│  - Windows 10/11/Server                                     │
│  - Python runtime                                           │
│  - ODBC drivers                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**This architecture provides a solid foundation for a production-ready web application with room for future enhancements and scalability.**
