# Phone Filter Configuration Update

## Change Summary

Removed "phone" from the `exclude_platforms` configuration setting in distributed INI files to allow discovery of phone devices.

## Problem

The default configuration was excluding devices with platform "phone" from network discovery, which prevented the discovery of IP phones and other phone-type devices that might be legitimate network infrastructure.

## Solution

Updated the filtering configuration to be more specific about phone exclusions:

### Before:
```ini
exclude_platforms = linux,windows,unix,freebsd,openbsd,netbsd,solaris,aix,hp-ux,vmware,docker,kubernetes,phone,host phone,camera,printer,access point,wireless,server
exclude_capabilities = host phone,ip phone,voip phone,camera,printer,server
```

### After:
```ini
exclude_platforms = linux,windows,unix,freebsd,openbsd,netbsd,solaris,aix,hp-ux,vmware,docker,kubernetes,host phone,camera,printer,access point,wireless,server
exclude_capabilities = host phone,camera,printer,server
```

## Changes Made

### 1. Configuration Template (netwalker/config/config_manager.py)
- **Removed**: "phone" from `exclude_platforms`
- **Removed**: "phone" from `exclude_capabilities` (kept "host phone")
- **Kept**: "host phone" in both settings to maintain filtering of host-type phones

### 2. Current Configuration File (netwalker.ini)
- **Removed**: "phone" from `exclude_platforms`
- **Removed**: "ip phone", "voip phone", and standalone "phone" from `exclude_capabilities`
- **Kept**: "host phone" to maintain appropriate filtering

### 3. Distributed Configuration (dist/NetWalker_v0.2.31/netwalker.ini)
- **Updated**: To match the new configuration standards
- **Ensured**: Consistency across all configuration files

## Impact

### Positive Changes:
- **IP Phones**: Will now be discovered if they support CDP/LLDP
- **Network Phones**: VoIP devices that are part of network infrastructure will be included
- **Phone Switches**: Devices with "phone" in their platform description will be discovered

### Maintained Filtering:
- **Host Phones**: Devices with "host phone" capability still excluded
- **End Devices**: Non-infrastructure phone devices still filtered appropriately
- **Other Exclusions**: All other platform and capability exclusions remain unchanged

## Testing

- ✅ Configuration property tests pass (3/3)
- ✅ Filter property tests pass (7/7)
- ✅ No breaking changes to existing functionality
- ✅ Configuration loading and validation working correctly

## Files Modified

1. `netwalker/config/config_manager.py` - Default configuration template
2. `netwalker.ini` - Current working configuration
3. `dist/NetWalker_v0.2.31/netwalker.ini` - Distributed configuration

## Backward Compatibility

This change is backward compatible. Existing installations can:
- Continue using their current configuration files
- Update their configuration manually if desired
- Get the new defaults when creating fresh configuration files

## Recommendation

For users who want to maintain the previous behavior (excluding all phone devices), they can manually add "phone" back to their `exclude_platforms` setting in their local `netwalker.ini` file.

## Next Steps

This change will be included in the next build and distribution package, ensuring that new installations have the updated filtering configuration by default.