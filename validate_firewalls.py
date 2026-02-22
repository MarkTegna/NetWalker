#!/usr/bin/env python3
"""
Validate firewalls from fw-disc.csv against database
Identifies missing and mis-identified devices
"""

import sys
import csv
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager


def main():
    """Main function"""
    
    # Load configuration
    config_file = 'netwalker.ini'
    config_manager = ConfigurationManager(config_file)
    parsed_config = config_manager.load_configuration()
    db_config = parsed_config.get('database', {})
    
    # Initialize database manager
    db_manager = DatabaseManager(db_config)
    
    if not db_manager.connect():
        print("[FAIL] Could not connect to database")
        return 1
    
    try:
        cursor = db_manager.connection.cursor()
        
        # Read firewalls from CSV
        print("\n" + "=" * 80)
        print("Firewall Validation Report")
        print("=" * 80)
        
        firewalls = []
        with open('fw-disc.csv', 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # Debug: print headers
            headers = reader.fieldnames
            print(f"\nCSV Headers: {headers}")
            
            for row in reader:
                # Handle different possible header names
                device_name = None
                ip_address = None
                
                for key in row.keys():
                    if 'device' in key.lower() and 'name' in key.lower():
                        device_name = row[key].strip()
                    elif 'ip' in key.lower() and 'address' in key.lower():
                        ip_address = row[key].strip()
                
                if device_name and ip_address:
                    firewalls.append({'name': device_name, 'ip': ip_address})
        
        print(f"\nTotal firewalls in CSV: {len(firewalls)}")
        
        # Check each firewall in database
        missing = []
        found_correct = []
        found_wrong_platform = []
        found_wrong_ip = []
        
        for fw in firewalls:
            # Query database for this device
            query = """
                SELECT 
                    d.device_name,
                    d.platform,
                    d.capabilities,
                    (SELECT TOP 1 ip_address
                     FROM device_interfaces
                     WHERE device_id = d.device_id
                     ORDER BY
                        CASE
                            WHEN interface_name LIKE '%Management%' THEN 1
                            WHEN interface_name LIKE '%Loopback%' THEN 2
                            WHEN interface_name LIKE '%Vlan%' THEN 3
                            ELSE 4
                        END,
                        interface_name) as ip_address,
                    d.status
                FROM devices d
                WHERE d.device_name = ?
            """
            
            cursor.execute(query, (fw['name'],))
            result = cursor.fetchone()
            
            if not result:
                missing.append(fw)
            else:
                device_name = result[0]
                platform = result[1] or 'Unknown'
                capabilities = result[2] or ''
                db_ip = result[3] or ''
                status = result[4]
                
                # Check if platform is correct (should be PAN-OS)
                if platform != 'PAN-OS':
                    found_wrong_platform.append({
                        'name': device_name,
                        'ip': fw['ip'],
                        'db_ip': db_ip,
                        'platform': platform,
                        'capabilities': capabilities,
                        'status': status
                    })
                # Check if IP matches
                elif db_ip != fw['ip']:
                    found_wrong_ip.append({
                        'name': device_name,
                        'expected_ip': fw['ip'],
                        'db_ip': db_ip,
                        'platform': platform,
                        'capabilities': capabilities,
                        'status': status
                    })
                else:
                    found_correct.append({
                        'name': device_name,
                        'ip': db_ip,
                        'platform': platform,
                        'capabilities': capabilities,
                        'status': status
                    })
        
        # Print summary
        print("\n" + "-" * 80)
        print("SUMMARY")
        print("-" * 80)
        print(f"Total firewalls in CSV:        {len(firewalls)}")
        print(f"Found with correct platform:   {len(found_correct)}")
        print(f"Found with wrong platform:     {len(found_wrong_platform)}")
        print(f"Found with wrong IP:           {len(found_wrong_ip)}")
        print(f"Missing from database:         {len(missing)}")
        
        # Print details
        if found_wrong_platform:
            print("\n" + "=" * 80)
            print("DEVICES WITH WRONG PLATFORM (Should be PAN-OS)")
            print("=" * 80)
            for device in found_wrong_platform:
                print(f"\n  Device: {device['name']}")
                print(f"  IP: {device['db_ip']}")
                print(f"  Platform: {device['platform']} (SHOULD BE: PAN-OS)")
                print(f"  Capabilities: {device['capabilities']}")
                print(f"  Status: {device['status']}")
        
        if found_wrong_ip:
            print("\n" + "=" * 80)
            print("DEVICES WITH WRONG IP ADDRESS")
            print("=" * 80)
            for device in found_wrong_ip:
                print(f"\n  Device: {device['name']}")
                print(f"  Expected IP: {device['expected_ip']}")
                print(f"  Database IP: {device['db_ip']}")
                print(f"  Platform: {device['platform']}")
        
        if missing:
            print("\n" + "=" * 80)
            print("MISSING DEVICES (Not in database)")
            print("=" * 80)
            
            # Create seed file for missing devices
            seed_file = "missing_firewalls_seed.csv"
            with open(seed_file, 'w') as f:
                for device in missing:
                    print(f"  {device['name']:30} {device['ip']}")
                    f.write(f"{device['ip']}\n")
            
            print(f"\n[OK] Created seed file for missing devices: {seed_file}")
            print(f"[OK] Total missing devices: {len(missing)}")
            print(f"\nTo discover missing devices, run:")
            print(f"  copy {seed_file} seed_file.csv")
            print(f"  .\\dist\\netwalker.exe --max-depth 0")
        
        # Print devices that need re-discovery
        if found_wrong_platform:
            print("\n" + "=" * 80)
            print("DEVICES NEEDING RE-DISCOVERY (Wrong Platform)")
            print("=" * 80)
            
            seed_file = "rediscover_firewalls_seed.csv"
            with open(seed_file, 'w') as f:
                for device in found_wrong_platform:
                    print(f"  {device['name']:30} {device['db_ip']}")
                    if device['db_ip']:
                        f.write(f"{device['db_ip']}\n")
            
            print(f"\n[OK] Created seed file for re-discovery: {seed_file}")
            print(f"[OK] Total devices needing re-discovery: {len(found_wrong_platform)}")
            print(f"\nTo re-discover these devices, run:")
            print(f"  copy {seed_file} seed_file.csv")
            print(f"  .\\dist\\netwalker.exe --max-depth 0")
        
        cursor.close()
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db_manager.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
