"""
Fix BACH_MINUET Device in Database

This script updates the BACH_MINUET device in the database with correct platform information.
"""

import pyodbc
from netwalker.config.config_manager import ConfigurationManager

def fix_bach_minuet_device():
    """Update BACH_MINUET device in database"""
    
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
        
        # Find BACH_MINUET device
        cursor.execute("""
            SELECT device_id, device_name, platform, hardware_model, capabilities
            FROM devices
            WHERE device_name LIKE '%BACH%MINUET%'
        """)
        
        device = cursor.fetchone()
        
        if not device:
            print("No BACH_MINUET device found in database")
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
        
        # Update with BACH_MINUET information
        new_platform = "BACH_MINUET"
        new_model = "BACH_MINUET Board"
        
        # No capabilities advertised in LLDP
        new_capabilities = None
        
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
        
        # Add firmware version information
        firmware_version = "v.2.3.2-b103-UN-ENCRYPTED"
        
        cursor.execute("""
            IF EXISTS (SELECT 1 FROM device_versions WHERE device_id = ?)
                UPDATE device_versions
                SET software_version = ?,
                    last_seen = GETDATE()
                WHERE device_id = ?
            ELSE
                INSERT INTO device_versions (device_id, software_version, last_seen)
                VALUES (?, ?, GETDATE())
        """, (device_id, firmware_version, device_id, device_id, firmware_version))
        
        print(f"  Firmware Version: {firmware_version}")
        print()
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"Successfully updated BACH_MINUET device")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_bach_minuet_device()
