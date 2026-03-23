"""
Query Paging Group Device Information

This script queries the database to find information about paging group devices
discovered via CDP/LLDP.
"""

import sys
import pyodbc
from netwalker.config.config_manager import ConfigurationManager

def query_paging_groups():
    """Query database for paging group device information"""
    
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
        
        # Query for paging group devices
        cursor.execute("""
            SELECT 
                d.device_id,
                d.device_name,
                d.serial_number,
                d.platform,
                d.hardware_model,
                d.capabilities,
                d.status,
                d.last_seen,
                dv.software_version,
                di.ip_address
            FROM devices d
            LEFT JOIN device_versions dv ON d.device_id = dv.device_id
            LEFT JOIN device_interfaces di ON d.device_id = di.device_id
            WHERE d.device_name LIKE '%paginggroup%'
            ORDER BY d.device_name, d.last_seen DESC
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No paging group devices found in database")
        else:
            print(f"Found {len(rows)} paging group device records:\n")
            
            for row in rows:
                print(f"Device ID: {row[0]}")
                print(f"Device Name: {row[1]}")
                print(f"Serial Number: {row[2]}")
                print(f"Platform: {row[3]}")
                print(f"Hardware Model: {row[4]}")
                print(f"Capabilities: {row[5]}")
                print(f"Status: {row[6]}")
                print(f"Last Seen: {row[7]}")
                print(f"Software Version: {row[8]}")
                print(f"IP Address: {row[9]}")
                print("-" * 80)
        
        # Query for neighbor connections to find parent devices
        print("\n" + "=" * 80)
        print("NEIGHBOR CONNECTIONS (to find parent devices):\n")
        
        cursor.execute("""
            SELECT 
                sd.device_name as source_device,
                dn.source_interface,
                dd.device_name as paging_group_device,
                dn.destination_interface,
                dn.protocol,
                dn.last_seen
            FROM device_neighbors dn
            INNER JOIN devices sd ON dn.source_device_id = sd.device_id
            INNER JOIN devices dd ON dn.destination_device_id = dd.device_id
            WHERE dd.device_name LIKE '%paginggroup%'
            ORDER BY dn.last_seen DESC
        """)
        
        neighbor_rows = cursor.fetchall()
        
        if not neighbor_rows:
            print("No neighbor connections found for paging group devices")
        else:
            print(f"Found {len(neighbor_rows)} neighbor connections:\n")
            
            for row in neighbor_rows:
                print(f"Parent Device: {row[0]}")
                print(f"Parent Interface: {row[1]}")
                print(f"Paging Group: {row[2]}")
                print(f"Paging Group Interface: {row[3]}")
                print(f"Protocol: {row[4]}")
                print(f"Last Seen: {row[5]}")
                print("-" * 80)
        
        cursor.close()
        connection.close()
        
        print("\n" + "=" * 80)
        print("\nTo see the raw CDP/LLDP data, you need to run discovery on the parent")
        print("device and check the log output for CDP/LLDP neighbor entries.")
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_paging_groups()
