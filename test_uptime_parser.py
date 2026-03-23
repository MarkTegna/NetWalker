#!/usr/bin/env python3
"""
Test the uptime parser function.
"""

import sys
sys.path.insert(0, '.')

from netwalker.database.database_manager import DatabaseManager

# Test cases
test_cases = [
    ("2 years, 45 weeks, 3 days, 14 hours, 32 minutes", None),
    ("15 weeks, 2 days, 15 hours, 37 minutes", None),
    ("123 day(s), 4 hour(s), 32 minute(s), 15 second(s)", None),
    ("142 days, 14:26:05", None),
    ("5 weeks, 2 days", None),
    ("3 hours, 45 minutes", None),
    ("1 year, 2 weeks, 3 days", None),
    ("Unknown", None),
    ("", None),
    (None, None),
]

print(f"\n{'='*80}")
print(f"UPTIME PARSER TEST")
print(f"{'='*80}")
print(f"{'Uptime String':<60} {'Total Hours':>12}")
print(f"{'-'*60} {'-'*12}")

for uptime_str, _ in test_cases:
    result = DatabaseManager.parse_uptime_to_hours(uptime_str or '')
    display_str = uptime_str if uptime_str else '(empty)'
    print(f"{display_str:<60} {str(result or 'None'):>12}")

print(f"\nAll tests completed.")
