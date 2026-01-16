import re

# Read the VLAN output from the log
vlan_output = """VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Te1/0/43, Te1/0/44, Te1/0/45, Te1/0/46, Te1/0/47, Twe1/1/1, Ap1/0/1, Ap2/0/1, Ap3/0/1, Te4/0/42, Te4/0/44, Te4/0/45, Te4/0/46, Te4/0/47, Twe4/1/1, Ap4/0/1
5    CISCO-MGMT                       active    
20   IPTV                             active    Tw1/0/2, Tw1/0/4, Tw1/0/6, Tw1/0/12, Tw1/0/16, Tw1/0/17, Tw1/0/21, Gi2/0/15, Gi2/0/26, Gi2/0/28, Gi2/0/36, Gi2/0/37, Gi3/0/1, Gi3/0/7, Gi3/0/9, Gi3/0/10, Gi3/0/11, Tw4/0/16, Tw4/0/32
98   CISCO_APs                        active    
100  CATO-LAN-01                      active    
101  CATO-LAN-02                      active    
112  19TH-FLOOR_CLIENTS               active    Tw1/0/1, Tw1/0/3, Tw1/0/7, Tw1/0/8, Tw1/0/9, Tw1/0/10, Tw1/0/11, Tw1/0/13, Tw1/0/14, Tw1/0/15, Tw1/0/18, Tw1/0/19, Tw1/0/20, Tw1/0/22, Tw1/0/23, Tw1/0/24, Tw1/0/25, Tw1/0/26, Tw1/0/27, Tw1/0/28, Tw1/0/29, Tw1/0/30, Tw1/0/31, Tw1/0/32, Tw1/0/33, Tw1/0/34, Tw1/0/35, Tw1/0/36, Gi2/0/1, Gi2/0/2, Gi2/0/3, Gi2/0/4, Gi2/0/5, Gi2/0/6, Gi2/0/7, Gi2/0/8, Gi2/0/9, Gi2/0/10, Gi2/0/11, Gi2/0/12, Gi2/0/13, Gi2/0/14, Gi2/0/16, Gi2/0/17, Gi2/0/18, Gi2/0/19, Gi2/0/20
216  RingCentral-Test                 active    Gi2/0/6, Gi2/0/31, Tw4/0/6, Tw4/0/23, Tw4/0/31
219  19TH-FLOOR_IPT_CLIENTS           active    Tw1/0/1, Tw1/0/3, Tw1/0/7, Tw1/0/8, Tw1/0/9, Tw1/0/10, Tw1/0/11, Tw1/0/13, Tw1/0/14, Tw1/0/15, Tw1/0/18, Tw1/0/19, Tw1/0/20, Tw1/0/22, Tw1/0/23, Tw1/0/24, Tw1/0/25, Tw1/0/26, Tw1/0/27, Tw1/0/28, Tw1/0/29, Tw1/0/30, Tw1/0/31, Tw1/0/32, Tw1/0/33, Tw1/0/34, Tw1/0/35, Tw1/0/36, Gi2/0/1, Gi2/0/2, Gi2/0/3, Gi2/0/4, Gi2/0/5, Gi2/0/7, Gi2/0/8, Gi2/0/9, Gi2/0/10, Gi2/0/11, Gi2/0/12, Gi2/0/13, Gi2/0/14, Gi2/0/16, Gi2/0/17, Gi2/0/18, Gi2/0/19, Gi2/0/20, Gi2/0/21
222  IPT_CISCO                        active    Gi2/0/47
456  FW_VENDOR                        active    Gi2/0/47, Gi3/0/48, Tw4/0/28
457  FW_VENDING_DMZ                   active    Tw1/0/5
461  FW-RINGCENTRAL                   active    
475  IPT                              active    Tw4/0/20"""

# Parse using the regex
ios_vlan_pattern = re.compile(
    r'^(\d+)\s+(\S+)\s+\S+\s+(.*)', 
    re.MULTILINE
)

vlans_with_ports = []
vlans_without_ports = []

for line in vlan_output.split('\n'):
    line = line.strip()
    if not line or 'VLAN Name' in line or '----' in line:
        continue
    
    match = ios_vlan_pattern.match(line)
    if match:
        vlan_id = int(match.group(1))
        vlan_name = match.group(2)
        ports_str = match.group(3).strip()
        
        if ports_str:
            vlans_with_ports.append((vlan_id, vlan_name))
        else:
            vlans_without_ports.append((vlan_id, vlan_name))

print("VLANs WITH ports:")
for vlan_id, vlan_name in vlans_with_ports:
    print(f"  VLAN {vlan_id}: {vlan_name}")

print(f"\nTotal VLANs with ports: {len(vlans_with_ports)}")

print("\n" + "=" * 80)
print("VLANs WITHOUT ports:")
for vlan_id, vlan_name in vlans_without_ports:
    print(f"  VLAN {vlan_id}: {vlan_name}")

print(f"\nTotal VLANs without ports: {len(vlans_without_ports)}")
print(f"\nTotal VLANs: {len(vlans_with_ports) + len(vlans_without_ports)}")
