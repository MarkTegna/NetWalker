# IPv4 Prefix Inventory - Integration Test Plan

## Overview

This document provides a comprehensive test plan for validating the IPv4 Prefix Inventory Module in a real network environment. Since Task 28 is optional and requires access to real network devices, this plan serves as a guide for manual testing and validation.

## Test Environment Requirements

### Network Devices

**Minimum Test Environment:**
- 1x Cisco IOS device (e.g., Cisco 2900 series router)
- 1x Cisco IOS-XE device (e.g., Cisco CSR1000v or Catalyst 9000)
- 1x Cisco NX-OS device (e.g., Nexus 9000 series switch)

**Recommended Test Environment:**
- 3x IOS devices with varying configurations
- 3x IOS-XE devices with VRFs configured
- 3x NX-OS devices with BGP configured
- Mix of devices with and without VRFs
- Mix of devices with and without BGP

### Device Configuration Requirements

**Device 1 - IOS Basic:**
- Global routing table with static routes
- Connected interfaces
- No VRFs
- No BGP

**Device 2 - IOS-XE with VRFs:**
- Global routing table
- 2-3 VRFs configured (e.g., MGMT, WAN, GUEST)
- BGP configured in global table
- BGP VPNv4 configured for VRFs
- Mix of static and dynamic routes

**Device 3 - NX-OS with BGP:**
- Global routing table
- 2-3 VRFs configured
- BGP configured in global and VRF tables
- Route summarization configured
- Multiple connected interfaces

### Infrastructure Requirements

- NetWalker database (SQL Server) accessible
- Network connectivity to all test devices
- Valid credentials for device access
- Sufficient disk space for output files (minimum 100MB)
- Python 3.8+ with all NetWalker dependencies installed

## Test Scenarios

### Scenario 1: Basic Collection (IOS Device)

**Objective:** Verify basic prefix collection from a simple IOS device

**Prerequisites:**
- IOS device with global routing table only
- No VRFs configured
- No BGP configured
- At least 5 routes in routing table

**Test Steps:**
1. Configure netwalker.ini:
   ```ini
   [ipv4_prefix_inventory]
   collect_global_table = true
   collect_per_vrf = false
   collect_bgp = false
   enable_database_storage = true
   ```

2. Run collection:
   ```bash
   python netwalker_app.py ipv4-prefix-inventory
   ```

3. Verify outputs:
   - Check `prefixes.csv` exists and contains routes
   - Check `prefixes_dedup_by_vrf.csv` exists
   - Check `exceptions.csv` exists (may be empty)
   - Check Excel file exists with 3 sheets
   - Check database table `ipv4_prefixes` has records

**Expected Results:**
- All connected interfaces appear as prefixes
- All static/dynamic routes appear as prefixes
- All prefixes tagged with vrf="global"
- All prefixes tagged with correct device name and platform
- No exceptions reported
- Database records created with correct timestamps

**Validation Queries:**
```sql
-- Check prefix count
SELECT COUNT(*) FROM ipv4_prefixes WHERE device_id = <device_id>;

-- Check VRF tagging
SELECT DISTINCT vrf FROM ipv4_prefixes WHERE device_id = <device_id>;
-- Should return only 'global'

-- Check sources
SELECT source, COUNT(*) FROM ipv4_prefixes WHERE device_id = <device_id> GROUP BY source;
```

---

### Scenario 2: VRF Collection (IOS-XE Device)

**Objective:** Verify per-VRF prefix collection

**Prerequisites:**
- IOS-XE device with 2-3 VRFs configured
- Each VRF has at least 3 routes
- Global table has routes

**Test Steps:**
1. Configure netwalker.ini:
   ```ini
   [ipv4_prefix_inventory]
   collect_global_table = true
   collect_per_vrf = true
   collect_bgp = false
   ```

2. Run collection

3. Verify VRF discovery:
   - Check logs for "Discovered VRFs: [list]"
   - Verify all configured VRFs are discovered

4. Verify per-VRF collection:
   - Check `prefixes.csv` contains routes from all VRFs
   - Verify each prefix is tagged with correct VRF name
   - Check deduplicated view groups by VRF

**Expected Results:**
- All VRFs discovered correctly
- Global table prefixes tagged with vrf="global"
- Per-VRF prefixes tagged with correct VRF names
- Deduplication maintains VRF separation
- No VRF-related exceptions

**Validation:**
```sql
-- Check VRF distribution
SELECT vrf, COUNT(*) FROM ipv4_prefixes 
WHERE device_id = <device_id> 
GROUP BY vrf;

-- Verify no cross-VRF contamination
SELECT * FROM ipv4_prefixes 
WHERE device_id = <device_id> AND vrf = 'MGMT';
-- All should be from MGMT VRF commands
```

---

### Scenario 3: BGP Collection (NX-OS Device)

**Objective:** Verify BGP prefix collection and ambiguity resolution

**Prerequisites:**
- NX-OS device with BGP configured
- BGP has learned routes
- Some BGP routes may lack explicit prefix length

**Test Steps:**
1. Configure netwalker.ini:
   ```ini
   [ipv4_prefix_inventory]
   collect_global_table = true
   collect_per_vrf = true
   collect_bgp = true
   ```

2. Run collection

3. Verify BGP collection:
   - Check logs for "Collecting BGP prefixes"
   - Verify BGP prefixes appear in output
   - Check for ambiguity resolution attempts

4. Check ambiguous prefix handling:
   - Review `exceptions.csv` for unresolved prefixes
   - Verify resolution attempts logged

**Expected Results:**
- BGP prefixes collected successfully
- Prefixes tagged with source="bgp"
- Ambiguous prefixes either resolved or recorded in exceptions
- Platform-specific BGP commands used (NX-OS: `show ip bgp vrf <VRF>`)

**Validation:**
```sql
-- Check BGP prefix count
SELECT COUNT(*) FROM ipv4_prefixes 
WHERE device_id = <device_id> AND source = 'bgp';

-- Check protocol tagging
SELECT protocol, COUNT(*) FROM ipv4_prefixes 
WHERE device_id = <device_id> AND source = 'bgp' 
GROUP BY protocol;
-- Should show 'B' for BGP routes
```

---

### Scenario 4: Route Summarization Tracking

**Objective:** Verify summarization relationship detection

**Prerequisites:**
- Device with route summarization configured
- Summary route and component routes both present
- Example: 192.168.0.0/16 summarizing 192.168.1.0/24, 192.168.2.0/24

**Test Steps:**
1. Configure netwalker.ini:
   ```ini
   [ipv4_prefix_inventory]
   track_summarization = true
   enable_database_storage = true
   ```

2. Run collection

3. Verify summarization detection:
   - Check database table `ipv4_prefix_summarization`
   - Verify relationships recorded

**Expected Results:**
- Summary routes identified
- Component routes linked to summaries
- Relationships stored in database with correct foreign keys
- Multi-level hierarchies tracked correctly

**Validation:**
```sql
-- Check summarization relationships
SELECT 
    s.prefix AS summary,
    c.prefix AS component,
    d.hostname AS device
FROM ipv4_prefix_summarization ps
JOIN ipv4_prefixes s ON ps.summary_prefix_id = s.prefix_id
JOIN ipv4_prefixes c ON ps.component_prefix_id = c.prefix_id
JOIN devices d ON ps.device_id = d.device_id
WHERE ps.device_id = <device_id>;

-- Verify component is within summary range
-- Manual verification: 192.168.1.0/24 should be within 192.168.0.0/16
```

---

### Scenario 5: Error Handling and Graceful Degradation

**Objective:** Verify error handling when commands fail

**Test Cases:**

**5a. BGP Not Configured:**
- Device without BGP
- Enable `collect_bgp = true`
- Expected: Warning logged, collection continues, no BGP prefixes

**5b. Invalid VRF Name:**
- Manually add invalid VRF to test
- Expected: Error logged, VRF skipped, other VRFs processed

**5c. Command Timeout:**
- Device with slow response
- Expected: Timeout logged, remaining commands attempted

**5d. Connection Failure:**
- Invalid credentials or unreachable device
- Expected: Device marked failed, other devices processed

**Test Steps:**
1. Configure scenarios above
2. Run collection
3. Check `exceptions.csv` for recorded errors
4. Verify collection continued despite errors

**Expected Results:**
- All errors logged appropriately
- Exceptions recorded in exceptions.csv
- Collection continues for other devices/commands
- Final summary shows success/failure counts

---

### Scenario 6: Concurrent Device Processing

**Objective:** Verify concurrent collection from multiple devices

**Prerequisites:**
- At least 5 devices accessible
- Mix of device types and configurations

**Test Steps:**
1. Configure netwalker.ini:
   ```ini
   [ipv4_prefix_inventory]
   concurrent_devices = 3
   ```

2. Run collection with timing:
   ```bash
   time python netwalker_app.py ipv4-prefix-inventory
   ```

3. Monitor logs for concurrent processing indicators

**Expected Results:**
- Multiple devices processed simultaneously
- Thread pool respects concurrency limit (max 3 concurrent)
- No thread interference or data corruption
- Results aggregated correctly from all devices
- Execution time less than sequential processing

**Validation:**
- Check log timestamps show overlapping device processing
- Verify all devices appear in final output
- Check database for records from all devices
- No duplicate or missing prefixes

---

### Scenario 7: Large-Scale Collection (Performance)

**Objective:** Verify performance with large dataset

**Prerequisites:**
- 10+ devices (or simulate with multiple collections)
- Devices with many routes (100+ per device)
- Multiple VRFs per device

**Test Steps:**
1. Configure for full collection:
   ```ini
   [ipv4_prefix_inventory]
   collect_global_table = true
   collect_per_vrf = true
   collect_bgp = true
   concurrent_devices = 5
   ```

2. Run collection with monitoring:
   ```bash
   time python netwalker_app.py ipv4-prefix-inventory
   ```

3. Monitor resource usage:
   - Memory consumption
   - CPU utilization
   - Disk I/O
   - Database connection count

**Expected Results:**
- Collection completes successfully
- Memory usage reasonable (<500MB for 10,000 prefixes)
- Execution time acceptable (<5 minutes for 10 devices)
- No memory leaks or resource exhaustion
- Database operations efficient (bulk inserts)

**Performance Targets:**
- 10 devices: <5 minutes
- 100 devices: <30 minutes
- 10,000 prefixes: <100MB memory
- Database inserts: >100 prefixes/second

---

### Scenario 8: Output Validation

**Objective:** Verify all output formats are correct

**Test Steps:**
1. Run full collection
2. Validate each output file

**CSV Validation:**
```python
import csv

# Check prefixes.csv
with open('prefixes.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    # Verify columns
    expected_cols = ['device', 'platform', 'vrf', 'prefix', 'source', 'protocol', 'timestamp']
    assert reader.fieldnames == expected_cols
    
    # Verify sort order (vrf, prefix, device)
    for i in range(len(rows)-1):
        assert (rows[i]['vrf'], rows[i]['prefix'], rows[i]['device']) <= \
               (rows[i+1]['vrf'], rows[i+1]['prefix'], rows[i+1]['device'])
    
    # Verify CIDR format
    import ipaddress
    for row in rows:
        ipaddress.ip_network(row['prefix'])  # Should not raise

# Check prefixes_dedup_by_vrf.csv
with open('prefixes_dedup_by_vrf.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    
    # Verify columns
    expected_cols = ['vrf', 'prefix', 'device_count', 'device_list']
    assert reader.fieldnames == expected_cols
    
    # Verify device_list format (semicolon-separated)
    for row in rows:
        devices = row['device_list'].split(';')
        assert int(row['device_count']) == len(devices)
```

**Excel Validation:**
```python
import openpyxl

wb = openpyxl.load_workbook('ipv4_prefix_inventory.xlsx')

# Verify sheets
assert 'Prefixes' in wb.sheetnames
assert 'Deduplicated' in wb.sheetnames
assert 'Exceptions' in wb.sheetnames

# Verify filters applied
ws = wb['Prefixes']
assert ws.auto_filter is not None

# Verify header formatting
header_row = ws[1]
for cell in header_row:
    assert cell.font.bold == True
```

**Database Validation:**
```sql
-- Verify schema
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME IN ('ipv4_prefixes', 'ipv4_prefix_summarization')
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- Verify foreign keys
SELECT 
    fk.name AS constraint_name,
    tp.name AS parent_table,
    cp.name AS parent_column,
    tr.name AS referenced_table,
    cr.name AS referenced_column
FROM sys.foreign_keys fk
INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
INNER JOIN sys.columns cp ON fkc.parent_column_id = cp.column_id AND fkc.parent_object_id = cp.object_id
INNER JOIN sys.columns cr ON fkc.referenced_column_id = cr.column_id AND fkc.referenced_object_id = cr.object_id
WHERE tp.name IN ('ipv4_prefixes', 'ipv4_prefix_summarization');

-- Verify data integrity
SELECT COUNT(*) FROM ipv4_prefixes WHERE device_id NOT IN (SELECT device_id FROM devices);
-- Should return 0

-- Verify timestamps
SELECT * FROM ipv4_prefixes WHERE first_seen > last_seen;
-- Should return 0 rows
```

---

## Integration Points Validation

### 1. Connection Manager Integration

**Test:** Verify connection reuse and management

```python
# Monitor connection pool
# Expected: Single connection per device, properly closed after use
```

**Validation:**
- No connection leaks
- Credentials properly applied
- SSH sessions properly terminated

### 2. Database Manager Integration

**Test:** Verify database operations

**Validation:**
- Schema created correctly
- Transactions properly committed
- Connection pooling works
- No SQL injection vulnerabilities

### 3. Configuration Manager Integration

**Test:** Verify configuration loading

**Validation:**
- All settings loaded from [ipv4_prefix_inventory] section
- Defaults applied when settings missing
- Invalid values handled gracefully

### 4. Excel Generator Integration

**Test:** Verify Excel export patterns

**Validation:**
- Consistent formatting with other NetWalker exports
- Proper use of ExcelGenerator class
- No library version conflicts

---

## Regression Testing

After any code changes, re-run these critical tests:

1. **Basic Collection** (Scenario 1) - Ensures core functionality works
2. **VRF Collection** (Scenario 2) - Ensures VRF handling works
3. **Error Handling** (Scenario 5) - Ensures graceful degradation
4. **Output Validation** (Scenario 8) - Ensures output formats correct

---

## Test Execution Checklist

### Pre-Test Setup
- [ ] NetWalker database accessible and empty (or use test database)
- [ ] All test devices accessible via SSH
- [ ] Valid credentials configured
- [ ] netwalker.ini configured correctly
- [ ] Output directory exists and writable
- [ ] Python environment has all dependencies

### Test Execution
- [ ] Scenario 1: Basic Collection - PASS/FAIL
- [ ] Scenario 2: VRF Collection - PASS/FAIL
- [ ] Scenario 3: BGP Collection - PASS/FAIL
- [ ] Scenario 4: Summarization Tracking - PASS/FAIL
- [ ] Scenario 5: Error Handling - PASS/FAIL
- [ ] Scenario 6: Concurrent Processing - PASS/FAIL
- [ ] Scenario 7: Performance Testing - PASS/FAIL
- [ ] Scenario 8: Output Validation - PASS/FAIL

### Post-Test Validation
- [ ] All output files generated correctly
- [ ] Database records accurate
- [ ] No errors in logs (except expected test errors)
- [ ] Memory usage acceptable
- [ ] Execution time acceptable
- [ ] No resource leaks

---

## Known Limitations

1. **Real Device Requirement:** This test plan requires access to real Cisco devices
2. **Time Investment:** Full test execution takes 2-4 hours
3. **Network Dependency:** Tests require stable network connectivity
4. **Device Configuration:** Devices must be pre-configured with appropriate test data

---

## Alternative: Mock-Based Integration Testing

For environments without real devices, see `test_integration_mock.py` for mock-based integration tests that validate:
- Component integration points
- Data flow through the system
- Error handling paths
- Output generation

Mock tests provide confidence in the integration without requiring real network devices.

---

## Success Criteria

The IPv4 Prefix Inventory Module is considered fully validated when:

1. ✅ All 8 test scenarios pass
2. ✅ All output formats validated
3. ✅ All integration points verified
4. ✅ Performance targets met
5. ✅ Error handling confirmed
6. ✅ Database integrity verified
7. ✅ No resource leaks detected
8. ✅ Documentation accurate and complete

---

## Appendix: Sample Device Configurations

### IOS Device Configuration
```
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 no shutdown

interface Loopback0
 ip address 10.0.0.1 255.255.255.255

ip route 172.16.0.0 255.255.0.0 192.168.1.254
```

### IOS-XE with VRFs
```
vrf definition MGMT
 address-family ipv4
 exit-address-family

vrf definition WAN
 address-family ipv4
 exit-address-family

interface GigabitEthernet1
 vrf forwarding MGMT
 ip address 10.1.1.1 255.255.255.0

interface GigabitEthernet2
 vrf forwarding WAN
 ip address 10.2.1.1 255.255.255.0

router bgp 65001
 address-family ipv4 vrf WAN
  network 10.2.0.0 mask 255.255.0.0
```

### NX-OS with BGP
```
vrf context MGMT
vrf context WAN

interface Ethernet1/1
 vrf member MGMT
 ip address 10.1.1.1/24

router bgp 65001
 vrf WAN
  address-family ipv4 unicast
   network 10.2.0.0/16
   aggregate-address 10.0.0.0/8 summary-only
```

---

**Document Version:** 1.0  
**Last Updated:** 2024  
**Author:** NetWalker Development Team
