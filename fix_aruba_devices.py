"""Fix Aruba AP devices in database - parse platform strings and update fields"""
import re
from netwalker.config.config_manager import ConfigurationManager
from netwalker.database import DatabaseManager

def parse_aruba_platform_string(platform_str):
    """Parse Aruba AP platform string to extract platform, model, and serial"""
    result = {
        'platform': platform_str,  # Default to full string
        'model': None,
        'serial': None
    }
    
    try:
        # Extract model number: "MODEL: 655" or "(MODEL: 655)"
        model_match = re.search(r'MODEL:\s*(\d+)', platform_str, re.IGNORECASE)
        if model_match:
            result['model'] = f"Aruba {model_match.group(1)}"
        
        # Extract serial number: "serial:PHSHKZ25TY" or "serial: PHSHKZ25TY"
        serial_match = re.search(r'serial:\s*([A-Z0-9]+)', platform_str, re.IGNORECASE)
        if serial_match:
            result['serial'] = serial_match.group(1)
        
        # Extract platform: "AOS-10" or "Aruba AP"
        if 'AOS-' in platform_str:
            aos_match = re.search(r'(AOS-\d+)', platform_str, re.IGNORECASE)
            if aos_match:
                result['platform'] = aos_match.group(1)
        elif 'Aruba AP' in platform_str:
            result['platform'] = 'Aruba AP'
        
    except Exception as e:
        print(f"Error parsing Aruba platform string: {e}")
    
    return result

def main():
    """Update all Aruba devices in database"""
    config_manager = ConfigurationManager()
    config = config_manager.load_configuration()
    
    # Initialize database manager
    db_config = config.get('database', {})
    db_manager = DatabaseManager(db_config)
    
    if not db_manager.connect():
        print("Failed to connect to database")
        return
    
    cursor = db_manager.connection.cursor()
    
    # Find all devices with Aruba platform strings that need parsing
    cursor.execute("""
        SELECT device_id, device_name, platform, hardware_model, serial_number
        FROM devices
        WHERE platform LIKE '%Aruba AP%' OR platform LIKE '%AOS-%'
    """)
    
    devices = cursor.fetchall()
    print(f"\nFound {len(devices)} Aruba devices to update\n")
    
    updated_count = 0
    
    for device in devices:
        device_id, device_name, platform, hardware_model, serial_number = device
        
        # Parse the platform string
        parsed = parse_aruba_platform_string(platform)
        
        print(f"Device: {device_name}")
        print(f"  Current Platform: {platform}")
        print(f"  Current Model: {hardware_model}")
        print(f"  Current Serial: {serial_number}")
        print(f"  New Platform: {parsed['platform']}")
        print(f"  New Model: {parsed['model']}")
        print(f"  New Serial: {parsed['serial']}")
        
        # Update the device
        update_fields = ["platform = ?", "updated_at = GETDATE()"]
        update_values = [parsed['platform']]
        
        if parsed['model'] and parsed['model'] != hardware_model:
            update_fields.append("hardware_model = ?")
            update_values.append(parsed['model'])
        
        if parsed['serial'] and parsed['serial'] != serial_number:
            update_fields.append("serial_number = ?")
            update_values.append(parsed['serial'])
        
        update_values.append(device_id)
        
        cursor.execute(f"""
            UPDATE devices
            SET {', '.join(update_fields)}
            WHERE device_id = ?
        """, tuple(update_values))
        
        updated_count += 1
        print(f"  ✓ Updated\n")
    
    db_manager.connection.commit()
    cursor.close()
    db_manager.disconnect()
    
    print(f"\nCompleted! Updated {updated_count} Aruba devices")

if __name__ == "__main__":
    main()
