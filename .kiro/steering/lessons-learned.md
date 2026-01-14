<!------------------------------------------------------------------------------------
   Add rules to this file or a short description that will apply across all your workspaces.
   
   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
------------------------------------------------------------------------------------> 

When running an executible in Powershell, you must start the command with .\

This test always fails and hangs Kiro, do not run it: cdp_walker/testing/test_resource_manager.py::TestResourceManagerProperties::test_context_manager_functionality

when starting a new test, clean out the old status entries in seed_file.csv to get a complete test, unless you are testing the resume function.

Copy the test_files into your working directory instead of pathing to them so that your updates do not carry over to the next test cycle.

Remove "Read-Host 'Press Enter to exit'" prompts from PowerShell build scripts to allow automated builds without user interaction.
Neighbor discovery failures can be caused by:
1. Credentials being None - add validation in connection manager and netwalker app initialization
2. Netmiko API changes - newer versions don't accept 'look_for_keys' parameter, use 'use_keys': False instead
3. Always validate credentials are not None before passing to connection methods

Unicode logging errors on Windows:
- Windows console uses cp1252 encoding which doesn't support Unicode box-drawing characters (║, ╔, ╚, ╠, ═) or symbols (✓, ✗)
- Replace Unicode characters with ASCII equivalents: ║ → |, ╔╚╠ → +, ═ → =, ✓ → [OK], ✗ → [FAIL]
- This prevents UnicodeEncodeError: 'charmap' codec can't encode character errors in logging
Additional netmiko compatibility issues:
- 'host_key_auto_add' parameter is not supported in current netmiko versions
- 'disabled_algorithms' parameter may also cause issues
- Keep netmiko device parameters minimal and stick to well-documented parameters
- For SSH host key issues, rely on system SSH configuration rather than netmiko parameters

Python bytecode cache issues:
- When running Python source code directly (not built executable), cached .pyc files in __pycache__ directories can cause old code to run
- Symptoms: Config files are correct, source code is correct, but behavior shows old code is executing
- Solution: Clear all __pycache__ directories and .pyc files using clear_python_cache.ps1
- Prevention: Use `python -B` flag during development to prevent bytecode generation, or always run built executables for testing
- If config changes don't take effect, always suspect cached bytecode first