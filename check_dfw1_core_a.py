#!/usr/bin/env python3
"""
Check DFW1-CORE-A device information extraction
"""

import re

# Sample NX-OS version output (typical format)
sample_nxos_output = """Cisco Nexus Operating System (NX-OS) Software
TAC support: http://www.cisco.com/tac
Copyright (C) 2002-2021, Cisco and/or its affiliates.
All rights reserved.
The copyrights to certain works contained in this software are
owned by other third parties and used and distributed under their own
licenses, such as open source.  This software is provided "as is," and unless
otherwise stated, there is no warranty, express or implied, including but not
limited to warranties of merchantability and fitness for a particular purpose.
Certain components of this software are licensed under
the GNU General Public License (GPL) version 2.0 or 
GNU General Public License (GPL) version 3.0  or the GNU
Lesser General Public License (LGPL) Version 2.1 or 
Lesser General Public License (LGPL) Version 2.0. 
A copy of each such license is available at
http://www.opensource.org/licenses/gpl-2.0.php and
http://opensource.org/licenses/gpl-3.0.html and
http://www.opensource.org/licenses/lgpl-2.1.php and
http://www.gnu.org/licenses/old-licenses/library.txt.

Software
  BIOS: version 08.38
 NXOS: version 9.3(9)
  BIOS compile time:  05/26/2020
  NXOS image file is: bootflash:///nxos.9.3.9.bin
  NXOS compile time:  10/28/2021 12:00:00 [10/28/2021 17:23:11]


Hardware
  cisco Nexus9000 C9396PX Chassis 
  Intel(R) Xeon(R) CPU E5-2403 v2 @ 1.80GHz with 16401316 kB of memory.
  Processor Board ID SAL1234ABCD

  Device name: DFW1-CORE-A
  bootflash:   53298520 kB
Kernel uptime is 123 day(s), 4 hour(s), 32 minute(s), 15 second(s)

Last reset 
  Reason: Reset Requested by CLI command reload
  System version: 9.3(9)
  Service: 

plugin
  Core Plugin, Ethernet Plugin

Active Package(s):
"""

# Test current extraction patterns
version_pattern = re.compile(r'Version\s+([^\s,]+)', re.IGNORECASE)
model_pattern = re.compile(r'Model [Nn]umber\s*:\s*([\w-]+)', re.IGNORECASE)

print("Testing version extraction:")
print("-" * 60)

# Test Version pattern (current)
version_match = version_pattern.search(sample_nxos_output)
if version_match:
    print(f"Current Version pattern found: {version_match.group(1)}")
else:
    print("Current Version pattern: NO MATCH")

# Test NX-OS specific pattern
nxos_version_pattern = re.compile(r'NXOS:\s+version\s+([^\s,]+)', re.IGNORECASE)
nxos_version_match = nxos_version_pattern.search(sample_nxos_output)
if nxos_version_match:
    print(f"NX-OS specific pattern found: {nxos_version_match.group(1)}")
else:
    print("NX-OS specific pattern: NO MATCH")

# Test System version pattern
system_version_pattern = re.compile(r'System version:\s+([^\s,]+)', re.IGNORECASE)
system_version_match = system_version_pattern.search(sample_nxos_output)
if system_version_match:
    print(f"System version pattern found: {system_version_match.group(1)}")
else:
    print("System version pattern: NO MATCH")

print("\n" + "=" * 60)
print("Testing hardware model extraction:")
print("-" * 60)

# Test Model Number pattern (current)
model_match = model_pattern.search(sample_nxos_output)
if model_match:
    print(f"Current Model Number pattern found: {model_match.group(1)}")
else:
    print("Current Model Number pattern: NO MATCH")

# Test Nexus chassis pattern
nexus_chassis_pattern = re.compile(r'cisco\s+Nexus\d+\s+(C\d+[A-Z]*)\s+Chassis', re.IGNORECASE)
nexus_chassis_match = nexus_chassis_pattern.search(sample_nxos_output)
if nexus_chassis_match:
    print(f"Nexus chassis pattern found: {nexus_chassis_match.group(1)}")
else:
    print("Nexus chassis pattern: NO MATCH")

# Test processor line pattern (for ISR routers)
processor_match = re.search(r'cisco\s+([\w-]+/[\w-]+)\s+\([^)]+\)\s+processor', sample_nxos_output, re.IGNORECASE)
if processor_match:
    print(f"Processor pattern found: {processor_match.group(1)}")
else:
    print("Processor pattern: NO MATCH")

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("-" * 60)
print("1. For NX-OS version: Use 'NXOS: version X.X(X)' pattern")
print("2. For NX-OS hardware: Use 'cisco NexusXXXX CXXXXXX Chassis' pattern")
print("3. Keep existing patterns as fallbacks for IOS/IOS-XE")
