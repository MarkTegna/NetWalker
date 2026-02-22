# Design Document: Stack Member Serial Number Update Bug Fix

## Overview

This design fixes a bug in the `upsert_stack_members()` method where serial numbers and hardware models are not updated when stack members are re-discovered. The bug occurs because the UPDATE SQL statement omits the `serial_number` and `hardware_model` fields, causing these values to remain "Unknown" even after successful enrichment.

## Root Cause Analysis

### Current Implementation

```python
# Update existing stack member
cursor.execute("""
    UPDATE device_stack_members
    SET role = ?,
        priority = ?,
        hardware_model = ?,  # MISSING!
        mac_address = ?,
        software_version = ?,
        state = ?,
        last_seen = GETDATE(),
        updated_at = GETDATE()
    WHERE stack_member_id = ?
""", (role, priority, hardware_model, mac_address, software_version, state, row[0]))
```

**Problem**: The UPDATE statement includes `hardware_model` in the SET clause but does NOT include `serial_number`. Additionally, the parameter list doesn't match - `hardware_model` is in the SET clause but the value isn't being passed correctly.

### Impact

1. Initial discovery creates stack members with serial_number = "Unknown"
2. Enrichment successfully collects serial numbers from "show inventory"
3. Database update ignores the enriched serial numbers
4. Stack members remain with "Unknown" serial numbers indefinitely

## Solution Design

### Approach 1: Add Missing Fields to UPDATE (Recommended)

Add `serial_number` and ensure `hardware_model` is properly updated in the UPDATE statement.

**Advantages:**
- Simple, minimal change
- Fixes the immediate bug
- Maintains existing logic flow

**Disadvantages:**
- May overwrite valid data with "Unknown" if enrichment fails

### Approach 2: Smart Update (Preserve Valid Data)

Only update fields when new value is not "Unknown" or when existing value is "Unknown".

**Advantages:**
- Prevents data corruption from partial failures
- More robust against transient collection issues
- Better data quality over time

**Disadvantages:**
- More complex logic
- Requires reading existing values before update

### Selected Approach

**Approach 1** (Add Missing Fields) for initial fix, with logging to detect issues. Can enhance to Approach 2 later if needed.

## Implementation

### Modified Method: `upsert_stack_members()`

**Location**: `netwalker/database/database_manager.py`

**Changes**:

1. Add `serial_number` to UPDATE statement
2. Ensure `hardware_model` is in correct position in parameter list
3. Add logging for updates

```python
def upsert_stack_members(self, device_id: int, stack_members: List) -> int:
    """
    Upsert stack members for a device
    
    Args:
        device_id: Database ID of the parent device
        stack_members: List of StackMemberInfo objects or dicts
        
    Returns:
        Number of stack members stored
    """
    if not self.enabled or not self.is_connected():
        return 0
    
    try:
        cursor = self.connection.cursor()
        member_count = 0
        
        for member in stack_members:
            # Handle both dict and object formats
            switch_number = member.get('switch_number') if hasattr(member, 'get') else getattr(member, 'switch_number')
            role = member.get('role') if hasattr(member, 'get') else getattr(member, 'role', None)
            priority = member.get('priority') if hasattr(member, 'get') else getattr(member, 'priority', None)
            hardware_model = member.get('hardware_model') if hasattr(member, 'get') else getattr(member, 'hardware_model')
            serial_number = member.get('serial_number') if hasattr(member, 'get') else getattr(member, 'serial_number')
            mac_address = member.get('mac_address') if hasattr(member, 'get') else getattr(member, 'mac_address', None)
            software_version = member.get('software_version') if hasattr(member, 'get') else getattr(member, 'software_version', None)
            state = member.get('state') if hasattr(member, 'get') else getattr(member, 'state', None)
            
            # Check if this stack member already exists
            cursor.execute("""
                SELECT stack_member_id, serial_number, hardware_model 
                FROM device_stack_members
                WHERE device_id = ? AND switch_number = ?
            """, (device_id, switch_number))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing stack member
                old_serial = row[1]
                old_model = row[2]
                
                # Log updates for debugging
                if old_serial != serial_number:
                    self.logger.info(f"Updating stack member {switch_number} serial: {old_serial} -> {serial_number}")
                if old_model != hardware_model:
                    self.logger.info(f"Updating stack member {switch_number} model: {old_model} -> {hardware_model}")
                
                cursor.execute("""
                    UPDATE device_stack_members
                    SET role = ?,
                        priority = ?,
                        hardware_model = ?,
                        serial_number = ?,
                        mac_address = ?,
                        software_version = ?,
                        state = ?,
                        last_seen = GETDATE(),
                        updated_at = GETDATE()
                    WHERE stack_member_id = ?
                """, (role, priority, hardware_model, serial_number, mac_address, 
                      software_version, state, row[0]))
            else:
                # Insert new stack member
                self.logger.info(f"Inserting new stack member {switch_number}: model={hardware_model}, serial={serial_number}")
                cursor.execute("""
                    INSERT INTO device_stack_members
                    (device_id, switch_number, role, priority, hardware_model, serial_number,
                     mac_address, software_version, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (device_id, switch_number, role, priority, hardware_model, serial_number,
                      mac_address, software_version, state))
            
            member_count += 1
        
        self.connection.commit()
        cursor.close()
        return member_count
        
    except pyodbc.Error as e:
        self.logger.error(f"Error upserting stack members: {e}")
        if self.connection:
            self.connection.rollback()
        return 0
```

### Key Changes

1. **Modified SELECT query**: Now retrieves existing `serial_number` and `hardware_model` for comparison
   - Changed from: `WHERE device_id = ? AND switch_number = ? AND serial_number = ?`
   - Changed to: `WHERE device_id = ? AND switch_number = ?`
   - Reason: The old query would fail to find existing records if serial changed

2. **Added `serial_number` to UPDATE**: Now updates serial number along with other fields

3. **Fixed parameter order**: Ensures `hardware_model` and `serial_number` are in correct positions

4. **Added logging**: Logs when serial or model values change for visibility

## Testing Strategy

### Unit Tests

1. **Test UPDATE with Unknown to Valid**
   - Create stack member with serial="Unknown", model="Unknown"
   - Update with serial="ABC123", model="C9300-48P"
   - Verify database contains new values

2. **Test UPDATE with Valid to Different Valid**
   - Create stack member with serial="ABC123", model="C9300-48P"
   - Update with serial="XYZ789", model="C9300-24P"
   - Verify database contains new values

3. **Test INSERT new member**
   - Insert stack member with all fields
   - Verify all fields stored correctly

4. **Test UPDATE other fields**
   - Update role, priority, state
   - Verify these fields update correctly

### Integration Tests

1. **Test full discovery cycle**
   - Discover device with stack
   - Verify initial "Unknown" values
   - Re-discover same device
   - Verify enriched values updated

2. **Test logging output**
   - Verify log messages show updates
   - Verify old and new values logged

## Rollback Plan

If issues arise:
1. Revert to previous version of `upsert_stack_members()`
2. Stack members will remain with "Unknown" values (existing behavior)
3. No data loss - only prevents updates

## Future Enhancements

### Smart Update (Approach 2)

If needed, implement logic to preserve valid data:

```python
# Only update if new value is not "Unknown" or existing is "Unknown"
if serial_number != "Unknown" or old_serial == "Unknown":
    # Update serial_number
else:
    # Keep existing value
    serial_number = old_serial
```

This would require:
- Reading existing values before update
- Conditional update logic
- More complex testing

## Correctness Properties

### Property 1: Serial Number Update Completeness

*For any* stack member with serial_number = "Unknown" in the database, when re-discovered with a valid serial number, the database should contain the new serial number after update.

**Validates: Requirement 1.1**

### Property 2: Hardware Model Update Completeness

*For any* stack member with hardware_model = "Unknown" in the database, when re-discovered with a valid hardware model, the database should contain the new hardware model after update.

**Validates: Requirement 2.1**

### Property 3: Update Idempotency

*For any* stack member, when updated multiple times with the same values, the database should contain those values and the update count should match the number of updates.

**Validates: Requirement 5.1, 5.2**

## Error Handling

### Database Errors

**UPDATE Failure**
- Symptom: pyodbc.Error during UPDATE
- Handling: Rollback transaction, log error, return 0
- Recovery: Next discovery will retry

**Connection Loss**
- Symptom: Connection closed during operation
- Handling: Rollback if possible, log error
- Recovery: Reconnect on next operation

### Data Validation

**Invalid Serial Format**
- Symptom: Serial number doesn't match expected pattern
- Handling: Store as-is (no validation in this fix)
- Note: Validation can be added later if needed

**Null Values**
- Symptom: serial_number or hardware_model is None
- Handling: Store as "Unknown" (existing behavior)
- Note: Database schema should handle NULL appropriately
