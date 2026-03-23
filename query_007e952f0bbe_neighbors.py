"""
Query Device 007e952f0bbe Neighbor Connections
"""

import pyodbc
from netwalker.config.config_manager import ConfigurationManager

def query_device_neighbors():
    """Query database for device 007e952f0bbe neighbor connections"""
    
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
        print("NEIGHBOR CONNECTIONS:\n")
        
        # Query for neighbor connections
        cursor.execute("""
            SELECT 
                sd.device_name as source_device,
                dn.source_interface,
                dd.device_name as target_device,
                dn.destination_interface,
                dn.protocol,
                dn.last_seen
            FROM device_neighbors dn
            INNER JOIN devices sd ON dn.source_device_id = sd.device_id
            INNER JOIN devices dd ON dn.destination_device_id = dd.device_id
            WHERE dd.device_name LIKE '%007e952f0bbe%'
            ORDER BY dn.last_seen DESC
        """)
        
        neighbor_rows = cursor.fetchall()
        
        if not neighbor_rows:
            print("No neighbor connections found for device 007e952f0bbe")
        else:
            print(f"Found {len(neighbor_rows)} neighbor connections:\n")
            
            parent_devices = set()
            for row in neighbor_rows:
                print(f"Parent Device: {row[0]}")
                print(f"Parent Interface: {row[1]}")
                print(f"Target Device: {row[2]}")
                print(f"Target Interface: {row[3]}")
                print(f"Protocol: {row[4]}")
                print(f"Last Seen: {row[5]}")
                print("-" * 80)
                parent_devices.add(row[0])
            
            print(f"\nUnique parent devices: {', '.join(sorted(parent_devices))}")
            print(f"\nTo get more information, run discovery on one of these parent devices")
            print(f"and check the CDP/LLDP output for device 007e952f0bbe")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_device_neighbors()
