"""
NetWalker Web Interface
A web-based front-end for querying the NetWalker database

Author: Mark Oldham
Version: 1.0.0
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc
from datetime import datetime, timedelta
import configparser
import base64
import os

app = Flask(__name__)

# Load configuration
def load_config():
    """Load configuration from config.ini if it exists, otherwise use defaults"""
    config = configparser.ConfigParser()
    
    # Default configuration
    db_config = {
        'server': 'eit-prisqldb01.tgna.tegna.com',
        'port': 1433,
        'database': 'NetWalker',
        'username': 'NetWalker',
        'password': 'FluffyBunnyHitbyaBus',
        'driver': 'ODBC Driver 17 for SQL Server'
    }
    
    web_config = {
        'host': '0.0.0.0',
        'port': 5000,
        'debug': True,
        'secret_key': os.urandom(24)
    }
    
    # Try to load from config.ini
    if os.path.exists('config.ini'):
        config.read('config.ini')
        
        if 'database' in config:
            db_config['server'] = config.get('database', 'server', fallback=db_config['server'])
            db_config['port'] = config.getint('database', 'port', fallback=db_config['port'])
            db_config['database'] = config.get('database', 'database', fallback=db_config['database'])
            db_config['username'] = config.get('database', 'username', fallback=db_config['username'])
            db_config['password'] = config.get('database', 'password', fallback=db_config['password'])
            db_config['driver'] = config.get('database', 'driver', fallback=db_config['driver'])
        
        if 'web' in config:
            web_config['host'] = config.get('web', 'host', fallback=web_config['host'])
            web_config['port'] = config.getint('web', 'port', fallback=web_config['port'])
            web_config['debug'] = config.getboolean('web', 'debug', fallback=web_config['debug'])
            secret_key = config.get('web', 'secret_key', fallback=None)
            if secret_key and secret_key != 'change-this-to-a-random-secret-key-in-production':
                web_config['secret_key'] = secret_key
    
    return db_config, web_config

DB_CONFIG, WEB_CONFIG = load_config()
app.secret_key = WEB_CONFIG['secret_key']

def get_connection():
    """Create database connection"""
    connection_string = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']},{DB_CONFIG['port']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)

@app.route('/')
def index():
    """Home page with dashboard statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
        device_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT vlan_number) FROM vlans")
        vlan_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM device_interfaces")
        interface_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT platform) FROM devices WHERE status = 'active'")
        platform_count = cursor.fetchone()[0]
        
        # Recent devices
        cursor.execute("""
            SELECT TOP 10 device_name, platform, last_seen
            FROM devices
            WHERE status = 'active'
            ORDER BY last_seen DESC
        """)
        recent_devices = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('index.html',
                             device_count=device_count,
                             vlan_count=vlan_count,
                             interface_count=interface_count,
                             platform_count=platform_count,
                             recent_devices=recent_devices)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('index.html',
                             device_count=0,
                             vlan_count=0,
                             interface_count=0,
                             platform_count=0,
                             recent_devices=[])

@app.route('/devices')
def devices():
    """List all devices with filtering"""
    platform = request.args.get('platform', '')
    search = request.args.get('search', '')
    status = request.args.get('status', 'active')
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT d.device_id, d.device_name, d.serial_number, d.platform, 
                   d.hardware_model, d.last_seen, d.status
            FROM devices d
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND d.status = ?"
            params.append(status)
        
        if platform:
            query += " AND d.platform = ?"
            params.append(platform)
        
        if search:
            query += " AND (d.device_name LIKE ? OR d.serial_number LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY d.device_name"
        
        cursor.execute(query, params)
        devices_list = cursor.fetchall()
        
        # Get platforms for filter dropdown
        cursor.execute("SELECT DISTINCT platform FROM devices WHERE platform IS NOT NULL ORDER BY platform")
        platforms = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return render_template('devices.html',
                             devices=devices_list,
                             platforms=platforms,
                             selected_platform=platform,
                             search=search,
                             status=status)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('devices.html', devices=[], platforms=[])

@app.route('/device/<int:device_id>')
def device_detail(device_id):
    """Device detail page"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get device info
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform, hardware_model,
                   first_seen, last_seen, status
            FROM devices
            WHERE device_id = ?
        """, (device_id,))
        device = cursor.fetchone()
        
        if not device:
            flash("Device not found", "error")
            return redirect(url_for('devices'))
        
        # Get current software version
        cursor.execute("""
            SELECT software_version, first_seen, last_seen
            FROM device_versions
            WHERE device_id = ?
            ORDER BY last_seen DESC
        """)
        versions = cursor.fetchall()
        
        # Get interfaces
        cursor.execute("""
            SELECT interface_name, ip_address, subnet_mask, interface_type, last_seen
            FROM device_interfaces
            WHERE device_id = ?
            ORDER BY interface_name
        """, (device_id,))
        interfaces = cursor.fetchall()
        
        # Get VLANs
        cursor.execute("""
            SELECT vlan_number, vlan_name, port_count, last_seen
            FROM device_vlans
            WHERE device_id = ?
            ORDER BY vlan_number
        """, (device_id,))
        vlans = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('device_detail.html',
                             device=device,
                             versions=versions,
                             interfaces=interfaces,
                             vlans=vlans)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return redirect(url_for('devices'))

@app.route('/vlans')
def vlans():
    """List all VLANs"""
    search = request.args.get('search', '')
    vlan_number = request.args.get('vlan_number', '')
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT v.vlan_id, v.vlan_number, v.vlan_name, v.last_seen,
                   COUNT(DISTINCT dv.device_id) as device_count,
                   SUM(dv.port_count) as total_ports
            FROM vlans v
            LEFT JOIN device_vlans dv ON v.vlan_id = dv.vlan_id
            WHERE 1=1
        """
        params = []
        
        if vlan_number:
            query += " AND v.vlan_number = ?"
            params.append(int(vlan_number))
        
        if search:
            query += " AND v.vlan_name LIKE ?"
            params.append(f'%{search}%')
        
        query += """
            GROUP BY v.vlan_id, v.vlan_number, v.vlan_name, v.last_seen
            ORDER BY v.vlan_number
        """
        
        cursor.execute(query, params)
        vlans_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('vlans.html',
                             vlans=vlans_list,
                             search=search,
                             vlan_number=vlan_number)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('vlans.html', vlans=[])

@app.route('/vlan/<int:vlan_id>')
def vlan_detail(vlan_id):
    """VLAN detail page"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get VLAN info
        cursor.execute("""
            SELECT vlan_id, vlan_number, vlan_name, first_seen, last_seen
            FROM vlans
            WHERE vlan_id = ?
        """, (vlan_id,))
        vlan = cursor.fetchone()
        
        if not vlan:
            flash("VLAN not found", "error")
            return redirect(url_for('vlans'))
        
        # Get devices with this VLAN
        cursor.execute("""
            SELECT d.device_id, d.device_name, d.platform, dv.port_count, dv.last_seen
            FROM device_vlans dv
            INNER JOIN devices d ON dv.device_id = d.device_id
            WHERE dv.vlan_id = ?
            AND d.status = 'active'
            ORDER BY d.device_name
        """, (vlan_id,))
        devices = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('vlan_detail.html',
                             vlan=vlan,
                             devices=devices)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return redirect(url_for('vlans'))

@app.route('/interfaces')
def interfaces():
    """List all interfaces"""
    search = request.args.get('search', '')
    interface_type = request.args.get('type', '')
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT di.interface_id, d.device_name, di.interface_name, 
                   di.ip_address, di.subnet_mask, di.interface_type, di.last_seen
            FROM device_interfaces di
            INNER JOIN devices d ON di.device_id = d.device_id
            WHERE d.status = 'active'
        """
        params = []
        
        if interface_type:
            query += " AND di.interface_type = ?"
            params.append(interface_type)
        
        if search:
            query += " AND (di.interface_name LIKE ? OR di.ip_address LIKE ? OR d.device_name LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY d.device_name, di.interface_name"
        
        cursor.execute(query, params)
        interfaces_list = cursor.fetchall()
        
        # Get interface types for filter
        cursor.execute("SELECT DISTINCT interface_type FROM device_interfaces WHERE interface_type IS NOT NULL ORDER BY interface_type")
        types = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return render_template('interfaces.html',
                             interfaces=interfaces_list,
                             types=types,
                             selected_type=interface_type,
                             search=search)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('interfaces.html', interfaces=[], types=[])

@app.route('/interface/<int:interface_id>')
def interface_detail(interface_id):
    """Interface detail page"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get interface info
        cursor.execute("""
            SELECT di.interface_id, d.device_id, d.device_name, di.interface_name,
                   di.ip_address, di.subnet_mask, di.interface_type,
                   di.first_seen, di.last_seen
            FROM device_interfaces di
            INNER JOIN devices d ON di.device_id = d.device_id
            WHERE di.interface_id = ?
        """, (interface_id,))
        interface = cursor.fetchone()
        
        if not interface:
            flash("Interface not found", "error")
            return redirect(url_for('interfaces'))
        
        cursor.close()
        conn.close()
        
        return render_template('interface_detail.html', interface=interface)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return redirect(url_for('interfaces'))

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/reports/platforms')
def report_platforms():
    """Platform distribution report"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT platform, COUNT(*) as device_count
            FROM devices
            WHERE status = 'active' AND platform IS NOT NULL
            GROUP BY platform
            ORDER BY device_count DESC
        """)
        platforms = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('report_platforms.html', platforms=platforms)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('report_platforms.html', platforms=[])

@app.route('/reports/software')
def report_software():
    """Software version distribution report"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT dv.software_version, COUNT(DISTINCT d.device_id) as device_count
            FROM device_versions dv
            INNER JOIN devices d ON dv.device_id = d.device_id
            WHERE d.status = 'active'
            AND dv.last_seen = (
                SELECT MAX(last_seen) 
                FROM device_versions 
                WHERE device_id = d.device_id
            )
            GROUP BY dv.software_version
            ORDER BY device_count DESC
        """)
        versions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('report_software.html', versions=versions)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('report_software.html', versions=[])

@app.route('/reports/stale')
def report_stale():
    """Stale devices report"""
    days = request.args.get('days', 30, type=int)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT device_name, platform, last_seen,
                   DATEDIFF(day, last_seen, GETDATE()) as days_ago
            FROM devices
            WHERE status = 'active'
            AND last_seen < DATEADD(day, ?, GETDATE())
            ORDER BY last_seen
        """, (-days,))
        devices = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('report_stale.html', devices=devices, days=days)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('report_stale.html', devices=[], days=days)

@app.route('/reports/vlan_consistency')
def report_vlan_consistency():
    """VLAN consistency report"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT vlan_number, 
                   COUNT(DISTINCT vlan_name) as name_count,
                   STRING_AGG(vlan_name, ', ') as names,
                   COUNT(DISTINCT device_id) as device_count
            FROM device_vlans
            GROUP BY vlan_number
            HAVING COUNT(DISTINCT vlan_name) > 1
            ORDER BY vlan_number
        """)
        inconsistent_vlans = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('report_vlan_consistency.html', vlans=inconsistent_vlans)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('report_vlan_consistency.html', vlans=[])

@app.route('/search')
def search():
    """Global search"""
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', query='', results={})
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        results = {}
        
        # Search devices
        cursor.execute("""
            SELECT device_id, device_name, serial_number, platform
            FROM devices
            WHERE device_name LIKE ? OR serial_number LIKE ?
            ORDER BY device_name
        """, (f'%{query}%', f'%{query}%'))
        results['devices'] = cursor.fetchall()
        
        # Search VLANs
        cursor.execute("""
            SELECT vlan_id, vlan_number, vlan_name
            FROM vlans
            WHERE vlan_name LIKE ? OR CAST(vlan_number AS VARCHAR) LIKE ?
            ORDER BY vlan_number
        """, (f'%{query}%', f'%{query}%'))
        results['vlans'] = cursor.fetchall()
        
        # Search interfaces by IP
        cursor.execute("""
            SELECT di.interface_id, d.device_name, di.interface_name, di.ip_address
            FROM device_interfaces di
            INNER JOIN devices d ON di.device_id = d.device_id
            WHERE di.ip_address LIKE ?
            ORDER BY d.device_name
        """, (f'%{query}%',))
        results['interfaces'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('search.html', query=query, results=results)
    except Exception as e:
        flash(f"Database error: {str(e)}", "error")
        return render_template('search.html', query=query, results={})

@app.template_filter('datetime_format')
def datetime_format(value, format='%Y-%m-%d %H:%M'):
    """Format datetime for display"""
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return value.strftime(format)

if __name__ == '__main__':
    print("=" * 50)
    print("NetWalker Web Interface v1.0.0")
    print("Author: Mark Oldham")
    print("=" * 50)
    print(f"\nStarting server on http://{WEB_CONFIG['host']}:{WEB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['server']} / {DB_CONFIG['database']}")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(
        debug=WEB_CONFIG['debug'],
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port']
    )
