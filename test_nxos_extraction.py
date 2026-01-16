#!/usr/bin/env python3
"""
Test NX-OS extraction with actual DeviceCollector methods
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from netwalker.discovery.device_collector import DeviceCollector

# Sample NX-OS output
nxos_output = """Cisco Nexus Operating System (NX-OS) Software
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

# Sample IOS-XE output (BORO-UW01)
ios_xe_output = """Cisco IOS XE Software, Version 17.12.06
Cisco IOS Software [Dublin], ISR Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 17.12.6, RELEASE SOFTWARE (fc3)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2024 by Cisco Systems, Inc.
Compiled Thu 21-Nov-24 12:34 by mcpre


Cisco IOS-XE software, Copyright (c) 2005-2024 by cisco Systems, Inc.
All rights reserved.  Certain components of Cisco IOS-XE software are
licensed under the GNU General Public License ("GPL") Version 2.0.  The
software code licensed under GPL Version 2.0 is free software that comes
with ABSOLUTELY NO WARRANTY.  You can redistribute and/or modify such
GPL code under the terms of GPL Version 2.0.  For more details, see the
documentation or "License Notice" file accompanying the IOS-XE software,
or the applicable URL provided on the flyer accompanying the IOS-XE
software.


ROM: IOS-XE ROMMON

BORO-UW01 uptime is 2 weeks, 3 days, 4 hours, 12 minutes
Uptime for this control processor is 2 weeks, 3 days, 4 hours, 14 minutes
System returned to ROM by reload
System image file is "bootflash:packages.conf"
Last reload reason: reload



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.


Technology Package License Information:

------------------------------------------------------------------------------
Technology-package                                     Technology-package
Current             Type                               Next reboot
------------------------------------------------------------------------------
network-advantage   Smart License                      network-advantage
dna-advantage       Subscription Smart License         dna-advantage


Smart Licensing Status: UNREGISTERED/No Licenses in Use

cisco ISR4451-X/K9 (OVLD-2RU) processor with 1685323K/6147K bytes of memory.
Processor board ID FLM2345ABCD
3 Gigabit Ethernet interfaces
32768K bytes of non-volatile configuration memory.
4194304K bytes of physical memory.
3207167K bytes of flash memory at bootflash:.
3088383K bytes of USB flash at usbflash0:.

Configuration register is 0x2102
"""

# Create collector
collector = DeviceCollector()

print("=" * 70)
print("Testing NX-OS Extraction (DFW1-CORE-A)")
print("=" * 70)

nxos_version = collector._extract_software_version(nxos_output)
nxos_model = collector._extract_hardware_model(nxos_output)

print(f"Software Version: {nxos_version}")
print(f"Expected: 9.3(9)")
print(f"✓ PASS" if nxos_version == "9.3(9)" else f"✗ FAIL")
print()

print(f"Hardware Model: {nxos_model}")
print(f"Expected: C9396PX")
print(f"✓ PASS" if nxos_model == "C9396PX" else f"✗ FAIL")
print()

print("=" * 70)
print("Testing IOS-XE Extraction (BORO-UW01)")
print("=" * 70)

ios_xe_version = collector._extract_software_version(ios_xe_output)
ios_xe_model = collector._extract_hardware_model(ios_xe_output)

print(f"Software Version: {ios_xe_version}")
print(f"Expected: 17.12.06")
print(f"✓ PASS" if ios_xe_version == "17.12.06" else f"✗ FAIL")
print()

print(f"Hardware Model: {ios_xe_model}")
print(f"Expected: ISR4451-X/K9")
print(f"✓ PASS" if ios_xe_model == "ISR4451-X/K9" else f"✗ FAIL")
print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
all_pass = (
    nxos_version == "9.3(9)" and
    nxos_model == "C9396PX" and
    ios_xe_version == "17.12.06" and
    ios_xe_model == "ISR4451-X/K9"
)

if all_pass:
    print("✓ ALL TESTS PASSED")
    sys.exit(0)
else:
    print("✗ SOME TESTS FAILED")
    sys.exit(1)
