#!/usr/bin/env python3
"""
Query database for LUMV-CORE-A device information
"""

import sys
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
        print("=" * 80)
        print("QUERYING DATABASE FOR LUMV-CORE-A")
        print("=" * 80)
        
        # Use the get_device_info_by_host method
        device_info = db_manager.get_device_info_by_host('LUMV-CORE-A')
        
        if device_info:
            print("\n[OK] Found device information:")
            print("-" * 80)
            print(f"Device ID:        {device_info.get('device_id', 'N/A')}")
            print(f"Hostname:         {device_info.get('hostname', 'N/A')}")
            print(f"Serial Number:    {device_info.get('serial_number', 'N/A')}")
            print(f"Hardware Model:   {device_info.get('hardware_model', 'N/A')}")
            print(f"Platform:         {device_info.get('platform', 'N/A')}")
            print(f"Software Version: {device_info.get('software_version', 'N/A')}")
            print(f"Primary IP:       {device_info.get('primary_ip', 'N/A')}")
            print(f"Status:           {device_info.get('status', 'N/A')}")
            print(f"Last Seen:        {device_info.get('last_seen', 'N/A')}")
            capabilities = device_info.get('capabilities', [])
            if capabilities:
                print(f"Capabilities:     {', '.join(capabilities)}")
            print("-" * 80)
            
            # Query additional details
            cursor = db_manager.connection.cursor()
            device_id = device_info['device_id']
            
            # Get all interfaces
            cursor.execute("""
                SELECT interface_name, ip_address, subnet_mask, interface_type, last_seen
                FROM device_interfaces
                WHERE device_id = ?
                ORDER BY last_seen DESC
            """, (device_id,))
            
            interfaces = cursor.fetchall()
            if interfaces:
                print("\nINTERFACES:")
                print("-" * 80)
                for intf in interfaces:
                    print(f"  {intf[0]:30} {intf[1]:20} /{intf[2] or 'N/A':15} ({intf[3] or 'N/A'})")
                    print(f"    Last Seen: {intf[4]}")
            
            # Get all versions
            cursor.execute("""
                SELECT software_version, first_seen, last_seen
                FROM device_versions
                WHERE device_id = ?
                ORDER BY last_seen DESC
            """, (device_id,))
            
            versions = cursor.fetchall()
            if versions:
                print("\nSOFTWARE VERSIONS:")
                print("-" * 80)
                for ver in versions:
                    print(f"  {ver[0]:40} First: {ver[1]}, Last: {ver[2]}")
            
            # Get stack members if any
            cursor.execute("""
                SELECT switch_number, role, priority, hardware_model, serial_number,
                       mac_address, software_version, state, last_seen
                FROM device_stack_members
                WHERE device_id = ?
                ORDER BY switch_number
            """, (device_id,))
            
            stack_members = cursor.fetchall()
            if stack_members:
                print("\nSTACK MEMBERS:")
                print("-" * 80)
                for member in stack_members:
                    print(f"  Switch {member[0]}: {member[3]} / SN: {member[4]}")
                    print(f"    Role: {member[1]}, Priority: {member[2]}, State: {member[7]}")
                    print(f"    MAC: {member[5]}, Software: {member[6]}")
                    print(f"    Last Seen: {member[8]}")
            
            cursor.close()
            print("=" * 80)
            
        else:
            print("\n[INFO] No device information found for LUMV-CORE-A")
            print("\nSearching for similar hostnames...")
            
            cursor = db_manager.connection.cursor()
            cursor.execute("""
                SELECT device_name, serial_number, platform, hardware_model, last_seen, status
                FROM devices
                WHERE device_name LIKE '%LUMV%' OR device_name LIKE '%LUM%'
                ORDER BY last_seen DESC
            """)
            
            similar = cursor.fetchall()
            if similar:
                print("\n[OK] Found similar devices:")
                print("-" * 80)
                for dev in similar:
                    print(f"  {dev[0]:30} {dev[2] or 'N/A':20} {dev[3] or 'N/A':20}")
                    print(f"    Serial: {dev[1]}, Status: {dev[5]}, Last: {dev[4]}")
            else:
                print("[INFO] No similar devices found")
            
            cursor.close()
            print("=" * 80)
        
    except Exception as e:
        print(f"\n[FAIL] Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db_manager.disconnect()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
