# NetWalker Testing Guide

## Overview
This guide explains how to test NetWalker with clean, real test data for consistent and reliable testing results.

## Author
Mark Oldham

## Clean Test Files Setup

### Why Use Clean Test Files?
- **Consistent Results**: Each test starts with the same clean data
- **Real Data**: Uses actual device names and credentials from production environment
- **No Contamination**: Previous test results don't affect new tests
- **Proper Testing**: Ensures CLI overrides work correctly

### Available Clean Test Files
Located in `prodtest_files/` directory:

1. **secret_test_creds.ini** - Clean credentials file with real test credentials
2. **seed_file.csv** - Clean seed devices file with real device names

## Setup Process

### Method 1: Python Script (Recommended)
```bash
python setup_clean_test_files.py
```

### Method 2: Batch Script
```bash
.\setup_clean_test_files.bat
```

### Method 3: Manual Copy
```bash
Copy-Item "prodtest_files/secret_test_creds.ini" "secret_creds.ini" -Force
Copy-Item "prodtest_files/seed_file.csv" "seed_file.csv" -Force
```

## Test Scenarios

### Test 1: Default File-Based Discovery
**Purpose**: Test that NetWalker uses seed devices from file when no CLI override provided

**Setup**:
```bash
python setup_clean_test_files.py
```

**Command**:
```bash
.\dist\netwalker\netwalker.exe --verbose
```

**Expected Results**:
- ✅ Loads seed devices from `seed_file.csv`
- ✅ Uses example device names: `CORE-SWITCH-A`, `CORE-SWITCH-B`
- ✅ Encrypts plain text credentials automatically
- ✅ Generates discovery reports

**Log Verification**:
```
INFO - Loaded 2 seed devices from seed_file.csv
INFO - Added seed device: CORE-SWITCH-A:CORE-SWITCH-A
INFO - Added seed device: CORE-SWITCH-B:CORE-SWITCH-B
INFO - Encrypted plain text password
```

### Test 2: CLI Override Discovery
**Purpose**: Test that CLI arguments override file-based seed devices

**Setup**:
```bash
python setup_clean_test_files.py
```

**Command**:
```bash
.\dist\netwalker\netwalker.exe --seed-devices "TEST-DEVICE:192.168.1.100" --verbose
```

**Expected Results**:
- ✅ Ignores seed devices from file
- ✅ Uses CLI-provided seed device: `TEST-DEVICE:192.168.1.100`
- ✅ Uses encrypted credentials from file
- ✅ Generates discovery reports

**Log Verification**:
```
INFO - Loaded 1 seed devices from CLI arguments
INFO - Added seed device: TEST-DEVICE:192.168.1.100
INFO - Using encrypted credentials
```

### Test 3: Multiple CLI Seed Devices
**Purpose**: Test multiple seed devices via CLI

**Setup**:
```bash
python setup_clean_test_files.py
```

**Command**:
```bash
.\dist\netwalker\netwalker.exe --seed-devices "DEVICE1:192.168.1.1,DEVICE2:192.168.1.2" --verbose
```

**Expected Results**:
- ✅ Uses both CLI-provided seed devices
- ✅ Processes devices in order
- ✅ Generates consolidated reports

### Test 4: Configuration Override
**Purpose**: Test other CLI configuration overrides

**Setup**:
```bash
python setup_clean_test_files.py
```

**Command**:
```bash
.\dist\netwalker\netwalker.exe --max-depth 3 --max-connections 5 --reports-dir ./test_reports --verbose
```

**Expected Results**:
- ✅ Uses file-based seed devices
- ✅ Applies CLI configuration overrides
- ✅ Creates reports in custom directory

## Test Data Details

### Clean Credentials (secret_creds.ini)
```ini
[credentials]
username = your_username
password = your_password
```

**Notes**:
- Plain text password will be automatically encrypted on first use
- File will be updated with encrypted password
- Encrypted format: `password = ENC:base64encodedstring`

### Clean Seed Devices (seed_file.csv)
```
CORE-SWITCH-A
CORE-SWITCH-B
```

**Notes**:
- Simple format: one device name per line
- No IP addresses specified (uses hostname for both name and IP)
- Real device names from production environment

## Testing Workflow

### Before Each Test Session
1. **Setup Clean Files**:
   ```bash
   python setup_clean_test_files.py
   ```

2. **Verify Clean State**:
   - Check that credentials are in plain text
   - Check that seed file contains only the two clean devices
   - No previous test artifacts in reports/logs directories

### During Testing
1. **Run Test Command**
2. **Monitor Logs**: Use `--verbose` flag for detailed logging
3. **Check Reports**: Verify Excel files are generated correctly
4. **Verify Behavior**: Confirm expected seed device loading behavior

### After Each Test
1. **Review Results**: Check discovery summary and reports
2. **Clean Up** (Optional): Remove generated reports/logs if needed
3. **Reset for Next Test**: Run setup script again for next test

## Common Issues and Solutions

### Issue: CLI Override Not Working
**Symptoms**: Application uses file devices instead of CLI devices
**Solution**: 
- Ensure you're using NetWalker v0.0.5 or later
- Verify CLI syntax: `--seed-devices "device:ip"`
- Check logs for "Loaded X seed devices from CLI arguments"

### Issue: Credentials Not Encrypting
**Symptoms**: Password remains in plain text
**Solution**:
- Ensure credentials file has proper INI format
- Check file permissions (should be writable)
- Verify `[credentials]` section exists

### Issue: No Seed Devices Found
**Symptoms**: "No seed devices configured" warning
**Solution**:
- Run setup script to copy clean files
- Verify seed_file.csv exists and has content
- Check file format (one device per line)

### Issue: Connection Failures
**Symptoms**: All devices show "Failed to discover"
**Note**: This is expected behavior in test environment
- Devices may not be reachable from test system
- Focus on testing seed device loading and CLI override behavior
- Connection failures don't indicate application problems

## Automation Scripts

### setup_clean_test_files.py
- **Purpose**: Copy clean test files and verify setup
- **Features**: File verification, content display, usage instructions
- **Usage**: `python setup_clean_test_files.py`

### setup_clean_test_files.bat
- **Purpose**: Quick batch script for Windows
- **Features**: Simple file copying with error checking
- **Usage**: `.\setup_clean_test_files.bat`

## Best Practices

1. **Always Start Clean**: Run setup script before each test session
2. **Use Verbose Logging**: Add `--verbose` flag to see detailed behavior
3. **Check Logs**: Verify seed device loading behavior in logs
4. **Test Both Scenarios**: File-based and CLI override modes
5. **Document Results**: Note any unexpected behavior or issues
6. **Clean Environment**: Use fresh test environment when possible

## Security Notes

- **Test Credentials**: The clean credentials are for testing only
- **Do Not Commit**: Never commit test credentials to version control
- **Local Use Only**: Test credentials should only exist in development environment
- **Encryption**: Application automatically encrypts plain text passwords

## Version Compatibility

- **NetWalker v0.0.5+**: Full CLI override support
- **NetWalker v0.0.3-0.0.4**: File priority issue (CLI override doesn't work)
- **Earlier Versions**: May have different behavior

Always use the latest version for testing to ensure all features work correctly.

---

**Author**: Mark Oldham  
**Last Updated**: 2026-01-11  
**NetWalker Version**: 0.0.5+