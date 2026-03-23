#!/usr/bin/env python3
"""
Check the schema of the devices table
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

        # Get column names for devices table
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'devices'
            ORDER BY ORDINAL_POSITION
        """)

        columns = cursor.fetchall()

        print("\nDevices table schema:")
        print("=" * 80)
        for col in columns:
            print(f"  {col[0]:<30} {col[1]:<20} Nullable: {col[2]}")
        print("=" * 80)

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
