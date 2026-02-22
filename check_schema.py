#!/usr/bin/env python3
"""
Check database schema for devices table
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
        
        # Get column information for devices table
        query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'devices'
            ORDER BY ORDINAL_POSITION
        """
        
        cursor.execute(query)
        columns = cursor.fetchall()
        
        print("\n" + "=" * 80)
        print("Devices Table Schema")
        print("=" * 80)
        print(f"\n{'Column Name':<30} {'Data Type':<20} {'Max Length':<15} {'Nullable':<10}")
        print("-" * 80)
        
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            max_length = col[2] if col[2] else 'N/A'
            nullable = col[3]
            print(f"{col_name:<30} {data_type:<20} {str(max_length):<15} {nullable:<10}")
        
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
