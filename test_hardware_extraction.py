"""Test hardware model extraction with BORO-UW01 output"""
import re

version_output = """Cisco IOS XE Software, Version 17.12.06
Cisco IOS Software [Dublin], ISR Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version 17.12.6, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2025 by Cisco Systems, Inc.
Compiled Sun 31-Aug-25 06:29 by mcpre

BORO-UW01 uptime is 15 weeks, 2 days, 15 hours, 37 minutes

cisco ISR4451-X/K9 (OVLD-2RU) processor with 3686327K/6147K bytes of memory.
Processor board ID FJC2230A1VZ
"""

# Test the new pattern
processor_match = re.search(r'cisco\s+([\w-]+/[\w-]+)\s+\([^)]+\)\s+processor', version_output, re.IGNORECASE)
if processor_match:
    print(f"✓ Extracted hardware model: {processor_match.group(1)}")
else:
    print("✗ Pattern did not match")
