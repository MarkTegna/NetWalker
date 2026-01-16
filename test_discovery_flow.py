#!/usr/bin/env python3
"""
Test the complete discovery flow to see where hardware_model gets lost
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from netwalker.discovery.device_collector import DeviceCollector
from netwalker.connection.data_models import DeviceInfo
from datetime import datetime

# Sample NX-OS output
nxos_output = """Cisco Nexus Operating System (NX-OS) Software
Software
  BIOS: version 08.38
 NXOS: version 9.3(9)

Hardware
  cisco Nexus9000 C9396PX Chassis 
  Processor Board ID FDO2324DFVE

  Device name: DFW1-CORE-A
Kernel uptime is 123 day(s), 4 hour(s), 32 minute(s), 15 second(s)

Last reset 
  System version: 9.3(9)
"""

print("=" * 70)
print("Step 1: Test DeviceCollector extraction")
print("=" * 70)

collector = DeviceCollector()

version = collector._extract_software_version(nxos_output)
model = collector._extract_hardware_model(nxos_output)

print(f"Software Version: {version}")
print(f"Hardware Model: {model}")
print()

print("=" * 70)
print("Step 2: Simulate DeviceInfo object creation")
print("=" * 70)

# Simulate what happens in collect_device_information
device_info = DeviceInfo(
    hostname="DFW1-CORE-A",
    primary_ip="172.26.128.2",
    platform="NX-OS",
    capabilities=["Router", "Switch"],
    software_version=version,
    vtp_version=None,
    serial_number="FDO2324DFVE",
    hardware_model=model,
    uptime="123 days",
    discovery_timestamp=datetime.now(),
    discovery_depth=0,
    is_seed=True,
    connection_method="SSH",
    connection_status="success",
    error_details=None,
    neighbors=[]
)

print(f"DeviceInfo.hardware_model: {device_info.hardware_model}")
print()

print("=" * 70)
print("Step 3: Simulate conversion to dictionary (discovery_engine.py line 656)")
print("=" * 70)

device_info_dict = {
    'hostname': device_info.hostname,
    'primary_ip': device_info.primary_ip,
    'platform': device_info.platform,
    'capabilities': device_info.capabilities,
    'software_version': device_info.software_version,
    'vtp_version': device_info.vtp_version,
    'serial_number': device_info.serial_number,
    'hardware_model': device_info.hardware_model,
    'uptime': device_info.uptime,
    'discovery_depth': device_info.discovery_depth,
    'discovery_method': 'seed',
    'parent_device': None,
    'discovery_timestamp': device_info.discovery_timestamp.isoformat(),
    'connection_method': device_info.connection_method,
    'connection_status': device_info.connection_status,
    'error_details': device_info.error_details,
    'neighbors': device_info.neighbors,
    'vlans': device_info.vlans,
    'vlan_collection_status': device_info.vlan_collection_status,
    'vlan_collection_error': device_info.vlan_collection_error
}

print(f"device_info_dict['hardware_model']: {device_info_dict['hardware_model']}")
print()

print("=" * 70)
print("Step 4: Simulate what excel_generator receives")
print("=" * 70)

# This is what would be in the inventory
inventory = {
    'DFW1-CORE-A:172.26.128.2': device_info_dict
}

for device_key, device_data in inventory.items():
    print(f"Device Key: {device_key}")
    print(f"  hostname: {device_data.get('hostname', '')}")
    print(f"  platform: {device_data.get('platform', '')}")
    print(f"  software_version: {device_data.get('software_version', '')}")
    print(f"  hardware_model: {device_data.get('hardware_model', '')}")
    print()

print("=" * 70)
print("CONCLUSION")
print("=" * 70)

if device_info_dict['hardware_model'] == model and model == "C9396PX":
    print("✓ Hardware model flows correctly through the entire pipeline")
    print("✓ The issue must be elsewhere (database, report generation, or caching)")
else:
    print("✗ Hardware model is lost somewhere in the pipeline")
    print(f"  Expected: C9396PX")
    print(f"  Got: {device_info_dict['hardware_model']}")
