"""Test if database manager is available in discovery engine"""
import logging
from netwalker.config.config_manager import ConfigurationManager
from netwalker.database.database_manager import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
config_manager = ConfigurationManager('netwalker.ini')
parsed_config = config_manager.load_configuration()
db_config = parsed_config.get('database', {})

logger.info(f"Database config: {db_config}")

# Create database manager
db_manager = DatabaseManager(db_config)

logger.info(f"DatabaseManager created:")
logger.info(f"  - enabled: {db_manager.enabled}")
logger.info(f"  - connection: {db_manager.connection}")

# Try to connect
if db_manager.enabled:
    logger.info("Attempting to connect...")
    if db_manager.connect():
        logger.info("Connected successfully!")
        logger.info(f"  - is_connected(): {db_manager.is_connected()}")
        
        # Test process_device_discovery with minimal data
        test_device = {
            'hostname': 'TEST-DEVICE',
            'serial_number': 'TEST123',
            'platform': 'IOS',
            'hardware_model': 'Test Model',
            'software_version': '1.0.0',
            'interfaces': [],
            'vlans': []
        }
        
        logger.info("Testing process_device_discovery...")
        result = db_manager.process_device_discovery(test_device)
        logger.info(f"  - Result: {result}")
        
        # Check database
        status = db_manager.get_database_status()
        logger.info(f"Database status after test:")
        logger.info(f"  - devices: {status['record_counts'].get('devices', 0)}")
        
        db_manager.disconnect()
    else:
        logger.error("Connection failed!")
else:
    logger.warning("Database not enabled")
