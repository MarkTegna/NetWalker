"""
PyInstaller hook for scrapli transport plugins
"""

from PyInstaller.utils.hooks import collect_all

# Collect all scrapli modules and data
datas, binaries, hiddenimports = collect_all('scrapli')

# Add transport plugin modules explicitly
transport_plugins = [
    'scrapli.transport.plugins.paramiko.transport',
    'scrapli.transport.plugins.ssh2.transport', 
    'scrapli.transport.plugins.asyncssh.transport',
    'scrapli.transport.plugins.system.transport',
    'scrapli.transport.plugins.telnet.transport',
]

hiddenimports.extend(transport_plugins)

# Add transport plugin dependencies
transport_deps = [
    'paramiko',
    'paramiko.client',
    'paramiko.transport',
    'paramiko.channel',
    'paramiko.ssh_exception',
    'ssh2',
    'ssh2.session',
    'ssh2.channel',
    'asyncssh',
    'asyncssh.connection',
    'asyncssh.client',
]

hiddenimports.extend(transport_deps)

# Add scrapli core modules
core_modules = [
    'scrapli.factory',
    'scrapli.driver.core.cisco_iosxe',
    'scrapli.driver.core.cisco_iosxr', 
    'scrapli.driver.core.cisco_nxos',
    'scrapli.driver.core.arista_eos',
    'scrapli.driver.core.juniper_junos',
    'scrapli.exceptions',
    'scrapli.response',
    'scrapli.channel',
    'scrapli.logging',
]

hiddenimports.extend(core_modules)