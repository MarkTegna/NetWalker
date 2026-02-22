#!/usr/bin/env python3
"""
Analyze core switches and count devices attached to each
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
        cursor = db_manager.connection.cursor()
        
        print("\n" + "=" * 80)
        print("Core Switch Device Count Analysis")
        print("=" * 80)
        
        # Find all core switches (devices with "CORE" in the name)
        core_query = """
            SELECT device_name
            FROM devices
            WHERE device_name LIKE '%CORE%'
            ORDER BY device_name
        """
        
        cursor.execute(core_query)
        core_switches = [row[0] for row in cursor.fetchall()]
        
        print(f"\nFound {len(core_switches)} core switches:")
        for core in core_switches:
            print(f"  - {core}")
        
        # For each core switch, count directly connected devices
        core_device_counts = {}
        
        for core_switch in core_switches:
            # Get the device_id for this core switch
            device_id_query = """
                SELECT device_id
                FROM devices
                WHERE device_name = ?
            """
            
            cursor.execute(device_id_query, (core_switch,))
            result = cursor.fetchone()
            
            if not result:
                core_device_counts[core_switch] = 0
                continue
            
            core_device_id = result[0]
            
            # Count unique devices that have this core switch as a neighbor
            # (devices where this core is the destination_device_id)
            neighbor_query = """
                SELECT COUNT(DISTINCT dn.source_device_id)
                FROM device_neighbors dn
                WHERE dn.destination_device_id = ?
                AND dn.source_device_id != ?
            """
            
            cursor.execute(neighbor_query, (core_device_id, core_device_id))
            count = cursor.fetchone()[0]
            core_device_counts[core_switch] = count
        
        # Sort by device count
        sorted_cores = sorted(core_device_counts.items(), key=lambda x: x[1])
        
        print("\n" + "-" * 80)
        print("Core Switches Ranked by Connected Device Count")
        print("-" * 80)
        print(f"{'Core Switch':<40} {'Connected Devices':>20}")
        print("-" * 80)
        
        for core_switch, count in sorted_cores:
            print(f"{core_switch:<40} {count:>20}")
        
        # Highlight the core with least devices
        if sorted_cores:
            least_core, least_count = sorted_cores[0]
            most_core, most_count = sorted_cores[-1]
            
            print("\n" + "=" * 80)
            print("Summary")
            print("=" * 80)
            print(f"\nCore with LEAST devices:  {least_core}")
            print(f"  Connected devices: {least_count}")
            print(f"\nCore with MOST devices:   {most_core}")
            print(f"  Connected devices: {most_count}")
            
            # Show devices connected to the core with least devices
            if least_count > 0:
                print(f"\n" + "-" * 80)
                print(f"Devices connected to {least_core}:")
                print("-" * 80)
                
                # Get the device_id for the least core
                device_id_query = """
                    SELECT device_id
                    FROM devices
                    WHERE device_name = ?
                """
                
                cursor.execute(device_id_query, (least_core,))
                least_core_id = cursor.fetchone()[0]
                
                devices_query = """
                    SELECT DISTINCT d.device_name, d.platform
                    FROM devices d
                    INNER JOIN device_neighbors dn ON d.device_id = dn.source_device_id
                    WHERE dn.destination_device_id = ?
                    AND d.device_id != ?
                    ORDER BY d.device_name
                """
                
                cursor.execute(devices_query, (least_core_id, least_core_id))
                connected_devices = cursor.fetchall()
                
                for device_name, platform in connected_devices:
                    platform_str = platform or 'Unknown'
                    print(f"  {device_name:<40} {platform_str}")
        
        print("\n" + "=" * 80)
        
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
