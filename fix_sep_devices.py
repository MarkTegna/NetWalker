"""
Fix Cisco IP Phone (SEP) Devices in Database

This script updates existing SEP devices in the database to have the correct
platform and capabilities.
"""

import pyodbc
from netwalker.config.config_manager import ConfigurationManager

def fix_sep_devices():
    """Update SEP devices in database"""
    
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
        
        # Find SEP devices that need updating (Unknown platform or Unwalked Neighbor model)
        cursor.execute("""
            SELECT device_id, device_name, platform, hardware_model, capabilities
            FROM devices
            WHERE device_name LIKE 'SEP%'
            AND (platform = 'Unknown' OR platform IS NULL 
                 OR hardware_model = 'Unwalked Neighbor' OR hardware_model IS NULL
                 OR capabilities IS NULL OR capabilities = '')
        """)
        
        devices = cursor.fetchall()
        
        if not devices:
            print("No SEP devices found that need updating")
            cursor.close()
            connection.close()
            return
        
        print(f"Found {len(devices)} SEP devices to update:\n")
        
        updated_count = 0
        
        for device in devices:
            device_id = device[0]
            device_name = device[1]
            current_platform = device[2]
            current_model = device[3]
            current_capabilities = device[4]
            
            print(f"Device: {device_name} (ID: {device_id})")
            print(f"  Current Platform: {current_platform}")
            print(f"  Current Model: {current_model}")
            print(f"  Current Capabilities: {current_capabilities}")
            
            # Update platform
            new_platform = "Cisco IP Phone"
            
            # Update hardware model
            new_model = "Cisco Unified IP Phone"
            
            # Add Phone capability
            capabilities_list = []
            if current_capabilities:
                capabilities_list = [c.strip() for c in current_capabilities.split(',')]
            
            if 'Phone' not in capabilities_list and 'phone' not in [c.lower() for c in capabilities_list]:
                capabilities_list.append('Phone')
            
            new_capabilities = ','.join(capabilities_list) if capabilities_list else 'Phone'
            
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
            
            updated_count += 1
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print(f"\n✓ Successfully updated {updated_count} SEP devices")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_sep_devices()
