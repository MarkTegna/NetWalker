#!/usr/bin/env python3
"""
Get count of network devices in the database
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
        
        # Get total device count
        cursor.execute("SELECT COUNT(*) FROM devices")
        total_count = cursor.fetchone()[0]
        
        # Get count by platform
        cursor.execute("""
            SELECT 
                ISNULL(platform, 'Unknown') as platform,
                COUNT(*) as count
            FROM devices
            GROUP BY platform
            ORDER BY COUNT(*) DESC
        """)
        
        platform_counts = cursor.fetchall()
        
        # Get count by status
        cursor.execute("""
            SELECT 
                ISNULL(status, 'Unknown') as status,
                COUNT(*) as count
            FROM devices
            GROUP BY status
            ORDER BY COUNT(*) DESC
        """)
        
        status_counts = cursor.fetchall()
        
        # Print results
        print("\n" + "=" * 80)
        print("Network Device Count Summary")
        print("=" * 80)
        print(f"\nTotal Devices: {total_count}")
        
        print("\n" + "-" * 80)
        print("Devices by Platform:")
        print("-" * 80)
        for platform, count in platform_counts:
            print(f"  {platform:30} {count:>6}")
        
        print("\n" + "-" * 80)
        print("Devices by Status:")
        print("-" * 80)
        for status, count in status_counts:
            print(f"  {status:30} {count:>6}")
        
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
