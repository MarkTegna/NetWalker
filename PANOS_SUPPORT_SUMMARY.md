# PAN-OS Firewall Support

## Summary
Added support for Palo Alto Networks firewalls running PAN-OS.

## Changes Made

### 1. Platform Detection (`device_collector.py`)
- Added PAN-OS detection in `_detect_platform()` method
- Detects PAN-OS by looking for "panos", "pan-os", or "sw-version:" in output
- Added logic to detect PAN-OS devices by checking for "-FW" in hostname prompt

### 2. Command Adaptation
- Modified device collection to use "show system info" for PAN-OS instead of "show version"
- Added "set cli pager off" command before collecting data from PAN-OS devices
- Skips VTP collection for PAN-OS (not applicable to firewalls)

### 3. Data Extraction
Added PAN-OS specific parsing patterns for:

**Hostname Extraction:**
- Pattern: `hostname: <value>`
- Example: `hostname: SITE-FW-01`

**Software Version:**
- Pattern: `sw-version: <value>`
- Example: `sw-version: 10.1.0`

**Serial Number:**
- Pattern: `serial: <value>`
- Example: `serial: 012345678901`

**Hardware Model:**
- Pattern: `model: <value>`
- Example: `model: PA-3220`

### 4. Capabilities
- PAN-OS devices are identified with capabilities: ["Firewall", "Router"]

### 5. Neighbor Discovery
- Skipped for PAN-OS devices (firewalls don't support CDP/LLDP)
- Future enhancement: Could use ARP tables with "show arp all" command

### 6. Stack Collection
- Skipped for PAN-OS (firewalls are not stackable)

## PAN-OS Commands Used

### Current Implementation:
```
set cli pager off
show system info
```

### Future Enhancements (not yet implemented):
```
show arp all          # For ARP table collection
show routing route    # For routing table collection
```

## Example PAN-OS "show system info" Output Format

```
hostname: SITE-FW-01
ip-address: 192.168.205.173
netmask: 255.255.255.0
default-gateway: 192.168.205.1
mac-address: 00:1b:17:00:01:23
time: Wed Feb 21 10:30:00 2026
uptime: 45 days, 12:34:56
family: 3200
model: PA-3220
serial: 012345678901
sw-version: 10.1.0
```

## Testing

### Test Device:
- IP: 192.168.205.173
- Expected hostname pattern: *-FW (e.g., SITE-FW-01)
- Platform: PAN-OS

### Expected Results:
1. Device detected as PAN-OS platform
2. Hostname extracted correctly
3. Software version shows PAN-OS version (e.g., 10.1.0)
4. Hardware model shows PA model (e.g., PA-3220)
5. Serial number extracted correctly
6. Capabilities show: Firewall, Router
7. No neighbor discovery attempted
8. No stack collection attempted

## Version
- Version 1.0.35
- Includes PAN-OS support

## Known Limitations
1. Neighbor discovery not implemented (PAN-OS doesn't support CDP/LLDP)
2. ARP table collection not yet implemented
3. Routing table collection not yet implemented

## Future Enhancements
1. Add ARP table collection using "show arp all"
2. Add routing table collection using "show routing route"
3. Add high availability (HA) pair detection
4. Add virtual system (VSYS) support for multi-tenant firewalls
