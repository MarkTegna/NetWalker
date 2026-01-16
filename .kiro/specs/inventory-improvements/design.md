# Design Document: Inventory and Credentials Improvements

## Overview

This design implements three improvements: filtering skipped devices from inventory sheets, discovering credential files in parent directory, and making enable password prompts optional.

## Architecture

### Component 1: Inventory Sheet Filtering
- Modify `excel_generator.py` to filter devices by status when creating inventory sheets
- Keep all devices in discovery sheets regardless of status

### Component 2: Parent Directory Credential Discovery
- Modify credential loading logic to check parent directory
- Search order: current directory → parent directory → default handling

### Component 3: Optional Enable Password
- Add configuration option to `netwalker.ini`
- Add CLI argument to `main.py`
- Modify credential prompt logic

## Components and Interfaces

### Modified Component: ExcelGenerator

**File**: `netwalker/reports/excel_generator.py`

**Modified Method**: `_create_device_inventory_sheet()`

**Changes**:
- Filter devices to exclude those with status "skipped"
- Only include devices with status in ["connected", "discovered", "success"]

### Modified Component: ConfigurationManager

**File**: `netwalker/config/config_manager.py`

**New Method**: `_find_credential_file(filename: str) -> Optional[str]`
- Check current directory for file
- Check parent directory (..\) for file
- Return path if found, None otherwise

**Modified Method**: `load_credentials()`
- Use `_find_credential_file()` to locate secret_creds.ini
- Log which location was used

### Modified Component: NetWalkerApp

**File**: `netwalker/netwalker_app.py`

**Modified Method**: `_prompt_for_credentials()`
- Check configuration for `prompt_for_enable_password`
- Check CLI args for `--enable-password` flag
- Only prompt if enabled

**File**: `main.py`

**New CLI Argument**: `--enable-password`
- Action: store_true
- Help: "Prompt for enable password"

## Data Models

### Configuration Addition

Add to `[credentials]` section in `netwalker.ini`:
```ini
[credentials]
# Prompt for enable password (true/false)
prompt_for_enable_password = false
```

## Implementation Details

### 1. Inventory Sheet Filtering

**Pseudocode**:
```python
def _create_device_inventory_sheet(workbook, inventory):
    # Filter devices to exclude skipped
    valid_statuses = ["connected", "discovered", "success"]
    filtered_inventory = {
        key: device for key, device in inventory.items()
        if device.get('status', '').lower() in valid_statuses
    }
    
    # Create sheet with filtered inventory
    # ... rest of sheet creation
```

### 2. Parent Directory Credential Discovery

**Pseudocode**:
```python
def _find_credential_file(filename):
    # Check current directory
    current_path = Path(filename)
    if current_path.exists():
        logger.info(f"Found {filename} in current directory")
        return str(current_path)
    
    # Check parent directory
    parent_path = Path("..") / filename
    if parent_path.exists():
        logger.info(f"Found {filename} in parent directory")
        return str(parent_path.absolute())
    
    return None

def load_credentials(config_file):
    # Try to find secret_creds.ini
    creds_path = _find_credential_file("secret_creds.ini")
    
    if creds_path:
        # Load from found location
        return load_from_file(creds_path)
    else:
        # Default handling
        return default_credentials()
```

### 3. Optional Enable Password

**Configuration**:
```ini
[credentials]
prompt_for_enable_password = false
```

**CLI Argument**:
```python
parser.add_argument('--enable-password', 
                   action='store_true',
                   help='Prompt for enable password')
```

**Prompt Logic**:
```python
def _prompt_for_credentials(config, cli_args):
    # Check if enable password prompt is needed
    prompt_enable = (
        config.get('credentials', {}).get('prompt_for_enable_password', False) or
        cli_args.enable_password
    )
    
    if prompt_enable:
        enable_pass = getpass.getpass("Enable password: ")
    else:
        enable_pass = None
    
    return credentials_with_enable(enable_pass)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do.*

### Property 1: Inventory Sheet Exclusion
*For any* device with status "skipped", that device should not appear in any Inventory sheet.

**Validates: Requirements 1.1, 1.3**

### Property 2: Discovery Sheet Inclusion
*For any* device regardless of status, that device should appear in the Discovery sheet.

**Validates: Requirements 1.2, 1.4**

### Property 3: Credential File Discovery Order
*For any* credential file search, the current directory should be checked before the parent directory.

**Validates: Requirements 2.1, 2.2**

### Property 4: Enable Password Default Behavior
*For any* execution without enable password configuration or CLI flag, the system should not prompt for enable password.

**Validates: Requirements 3.1, 3.3**

## Error Handling

- If parent directory credential file is unreadable, log warning and continue
- If enable password prompt fails, continue without enable password
- If inventory filtering removes all devices, create empty inventory sheet with headers

## Testing Strategy

### Unit Tests

1. **Inventory Filtering**
   - Test with mixed device statuses
   - Verify skipped devices excluded from inventory
   - Verify all devices in discovery sheet

2. **Credential File Discovery**
   - Test with file in current directory
   - Test with file in parent directory
   - Test with file in both locations (current takes precedence)
   - Test with file in neither location

3. **Enable Password Prompt**
   - Test with config=false, cli=false → no prompt
   - Test with config=true, cli=false → prompt
   - Test with config=false, cli=true → prompt
   - Test with config=true, cli=true → prompt

### Integration Tests

- Run discovery with skipped devices, verify inventory sheet
- Run with credential file in parent directory
- Run with --enable-password flag

### Testing Configuration

- Unit tests for each component
- Integration tests for end-to-end behavior
- Both types of tests are required for comprehensive coverage
