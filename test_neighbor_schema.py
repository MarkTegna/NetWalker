"""
Test script to verify device_neighbors table schema
"""

import sys
from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager

def main():
    print("=" * 70)
    print("Testing device_neighbors table schema")
    print("=" * 70)
    print()
    
    # Load configuration
    config_manager = ConfigurationManager('netwalker.ini')
    parsed_config = config_manager.load_configuration()
    db_config = parsed_config.get('database', {})
    
    # Initialize database manager
    print("Connecting to database...")
    db_manager = DatabaseManager(db_config)
    
    if not db_manager.connect():
        print("[FAIL] Could not connect to database")
        return 1
    
    print("[OK] Connected to database")
    print()
    
    # Initialize database (create tables if they don't exist)
    print("Initializing database schema...")
    if db_manager.initialize_database():
        print("[OK] Database schema initialized")
    else:
        print("[FAIL] Failed to initialize database schema")
        return 1
    
    print()
    
    # Check if device_neighbors table exists
    print("Checking device_neighbors table...")
    cursor = db_manager.connection.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'device_neighbors'
        """)
        
        count = cursor.fetchone()[0]
        
        if count == 1:
            print("[OK] device_neighbors table exists")
        else:
            print("[FAIL] device_neighbors table not found")
            return 1
        
        # Get table schema
        print()
        print("Table schema:")
        cursor.execute("""
            SELECT 
                COLUMN_NAME, 
                DATA_TYPE, 
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'device_neighbors'
            ORDER BY ORDINAL_POSITION
        """)
        
        for row in cursor.fetchall():
            col_name = row[0]
            data_type = row[1]
            max_length = row[2] if row[2] else ''
            nullable = row[3]
            
            if max_length:
                print(f"  {col_name}: {data_type}({max_length}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            else:
                print(f"  {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
        
        # Check indexes
        print()
        print("Indexes:")
        cursor.execute("""
            SELECT 
                i.name AS index_name,
                COL_NAME(ic.object_id, ic.column_id) AS column_name
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            WHERE i.object_id = OBJECT_ID('device_neighbors')
            ORDER BY i.name, ic.key_ordinal
        """)
        
        current_index = None
        for row in cursor.fetchall():
            index_name = row[0]
            column_name = row[1]
            
            if index_name != current_index:
                print(f"  {index_name}: {column_name}")
                current_index = index_name
            else:
                print(f"    + {column_name}")
        
        # Check foreign keys
        print()
        print("Foreign keys:")
        cursor.execute("""
            SELECT 
                fk.name AS constraint_name,
                OBJECT_NAME(fk.parent_object_id) AS table_name,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS column_name,
                OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS referenced_column,
                fk.delete_referential_action_desc AS delete_action
            FROM sys.foreign_keys fk
            INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            WHERE fk.parent_object_id = OBJECT_ID('device_neighbors')
        """)
        
        for row in cursor.fetchall():
            constraint_name = row[0]
            table_name = row[1]
            column_name = row[2]
            ref_table = row[3]
            ref_column = row[4]
            delete_action = row[5]
            
            print(f"  {constraint_name}:")
            print(f"    {table_name}.{column_name} -> {ref_table}.{ref_column}")
            print(f"    ON DELETE {delete_action}")
        
        cursor.close()
        
    except Exception as e:
        print(f"[FAIL] Error checking table: {e}")
        return 1
    
    # Disconnect
    db_manager.disconnect()
    print()
    print("[OK] All checks passed!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
