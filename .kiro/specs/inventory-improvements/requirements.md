# Requirements Document: Inventory and Credentials Improvements

## Introduction

NetWalker needs improvements to inventory reporting, credential file discovery, and enable password handling to provide more accurate reports and better user experience.

## Glossary

- **Inventory_Sheet**: Excel sheet containing device inventory with complete information
- **Discovery_Sheet**: Excel sheet containing all discovery attempts including failures
- **Skipped_Device**: Device that was discovered but not fully inventoried (incomplete data)
- **Secret_Creds_File**: Credentials configuration file (secret_creds.ini)
- **Enable_Password**: Cisco enable mode password for privileged access
- **CLI**: Command Line Interface
- **INI_File**: Configuration file in INI format

## Requirements

### Requirement 1: Exclude Skipped Devices from Inventory Sheets

**User Story:** As a network administrator, I want skipped devices excluded from inventory sheets, so that I only see devices with complete and accurate information in my inventory reports.

#### Acceptance Criteria

1. WHEN a device has status "skipped", THE System SHALL exclude it from the Inventory sheet
2. WHEN a device has status "skipped", THE System SHALL include it in the Discovery sheet
3. WHEN generating Inventory sheets, THE System SHALL only include devices with status "connected" or "discovered"
4. THE System SHALL maintain all device information in Discovery sheets regardless of status

### Requirement 2: Parent Directory Credential File Discovery

**User Story:** As a user, I want NetWalker to check the parent directory for secret_creds.ini, so that I can share credentials across multiple NetWalker installations without duplicating files.

#### Acceptance Criteria

1. WHEN loading credentials, THE System SHALL first check the current directory for secret_creds.ini
2. WHEN secret_creds.ini is not found in current directory, THE System SHALL check the parent directory (..\)
3. WHEN secret_creds.ini is found in parent directory, THE System SHALL load credentials from that file
4. WHEN secret_creds.ini is not found in either location, THE System SHALL proceed with default credential handling

### Requirement 3: Optional Enable Password Prompt

**User Story:** As a user, I want to control whether NetWalker prompts for an enable password, so that I can avoid unnecessary prompts when enable passwords are not needed.

#### Acceptance Criteria

1. THE System SHALL provide an INI configuration option "prompt_for_enable_password" with default value "false"
2. THE System SHALL provide a CLI option "--enable-password" to override the INI setting
3. WHEN prompt_for_enable_password is false AND no CLI option is provided, THE System SHALL NOT prompt for enable password
4. WHEN prompt_for_enable_password is true OR CLI option is provided, THE System SHALL prompt for enable password
5. WHEN enable password is not provided, THE System SHALL proceed without enable password
