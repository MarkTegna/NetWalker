"""
Find Trio devices in database
"""
import sys
sys.path.insert(0, '.')

from netwalker.config.config_manager import ConfigurationManager
from netwalker.database.database_manager import DatabaseManager

config_manager = ConfigurationManager('netwalker.ini')
full_config = config_manager.load_configuration()
db_config = full_config.get('database', {})

db = DatabaseManager(db_config)
db.connect()

cursor = db.connection.cursor()
cursor.execute("""
    SELECT device_id, device_name, platform, hardware_model
    FROM devices 
    WHERE device_name LIKE '%Trio%' OR platform LIKE '%Trio%'
""")

rows = cursor.fetchall()
if rows:
    print(f'Found {len(rows)} Trio device(s):\n')
    for row in rows:
        print(f'Device: {row[1]} (ID: {row[0]})')
        print(f'  Platform: {row[2]}')
        print(f'  Hardware Model: {row[3]}')
        print()
else:
    print('No Trio devices found')

cursor.close()
db.disconnect()
