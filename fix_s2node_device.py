"""
Fix s2node Device in Database

This script updates the s2node device in the database with correct platform information.
"""

import pyodbc
from netwalker.config.config_manager import ConfigurationManager

def fix_s2node_device():
    """Update s2node device in database"""
    
    # Load configuration
    config_manager = ConfigurationManager('netwalker.ini')
    config = config_manager.load_configuration()
    db_config = config['database']
    
    if not db_config.get('enabled'):
        print("Database is not enabled in configuration")
        return
    
    # Connect to database
    try:
        server = db_config.get('server')
        port = db_config.get('port', 1433)
        database = db_config.get('database', 'NetWalker')
        username = db_config.get('username')
        password = db_config.get('password')
        trust_cert = db_config.get('trust_server_certificate', True)
        
        # Find available driver
        available_drivers = pyodbc.drivers()
        sql_drivers = [d for d in available_drivers if 'SQL Server' in d]
        
        if not sql_drivers:
            print("No SQL Server ODBC driver found")
            return
        
        driver = None
        for preferred in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
            if preferred in sql_drivers:
                driver = preferred
                break
        
        if not driver:
            driver = sql_drivers[0]
        
        print(f"Using ODBC driver: {driver}")
        
        # Build connection string
        if 'ODBC Driver 1' in driver:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"TrustServerCertificate={'yes' if trust_cert else 'no'};"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
            )
        
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()
        
        print(f"\nConnected to database: {server}/{database}\n")
        print("=" * 80)
        
        # Find s2node device
        cursor.execute("""
            SELECT device_id, device_name, platform, hardware_model, capabilities
            FROM devices
            WHERE device_name = 's2node'
        """)
        
        device = cursor.fetchone()
        
        if not device:
            print("No s2node device found in database")
            cursor.close()
            connection.close()
            return
        
        device_id = device[0]
        device_name = device[1]
        current_platform = device[2]
        current_model = device[3]
        current_capabilities = device[4]
        
        print(f"Device: {device_name} (ID: {device_id})")
        print(f"  Current Platform: {current_platform}")
        print(f"  Current Model: {current_model}")
        print(f"  Current Capabilities: {current_capabilities}")
        print()
        
        # Update with Linux embedded device information
        new_platform = "Linux"
        new_model = "Embedded Linux Device (ARM v7)"
        
        # Parse capabilities from LLDP: B=Bridge, W=WLAN, R=Router, S=Station
        new_capabilities = "Bridge,WLAN,Router,Station"
        
        # Update device
        cursor.execute("""
            UPDATE devices
            SET platform = ?,
                hardware_model = ?,
                capabilities = ?,
                updated_at = GETDATE()
            WHERE device_id = ?
        """, (new_platform, new_model, new_capabilities, device_id))
        
        print(f"  New Platform: {new_platform}")
        print(f"  New Model: {new_model}")
        print(f"  New Capabilities: {new_capabilities}")
        print("-" * 80)
        
        # Add software version information
        software_version = "Linux 3.13.0-ts-armv7l (2014-12-11)"
        
        cursor.execute("""
            IF EXISTS (SELECT 1 FROM device_versions WHERE device_id = ?)
                UPDATE device_versions
                SET software_version = ?,
                    last_seen = GETDATE()
                WHERE device_id = ?
            ELSE
                INSERT INTO device_versions (device_id, software_version, last_seen)
                VALUES (?, ?, GETDATE())
        """, (device_id, software_version, device_id, device_id, software_version))
        
        print(f"  Software Version: {software_version}")
        print()
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Successfully updated s2node device")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_s2node_device()
