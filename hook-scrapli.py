# PyInstaller hook for scrapli and netmiko

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all scrapli modules and data
datas, binaries, hiddenimports = collect_all('scrapli')

# Add specific transport plugin modules (telnet and system only for scrapli)
transport_modules = [
    'scrapli.transport.plugins.telnet.transport',
    'scrapli.transport.plugins.system.transport',
]

for module in transport_modules:
    try:
        hiddenimports.extend(collect_submodules(module))
    except:
        pass

# Add netmiko dependencies
try:
    netmiko_datas, netmiko_binaries, netmiko_hiddenimports = collect_all('netmiko')
    datas.extend(netmiko_datas)
    binaries.extend(netmiko_binaries)
    hiddenimports.extend(netmiko_hiddenimports)
except:
    pass