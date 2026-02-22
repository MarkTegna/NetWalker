"""
Test script for Task 7: Checkpoint - Ensure collection components work

This script verifies that all collection components (VRF discovery, routing table
collection, BGP collection, pagination control) are working correctly.

Author: Mark Oldham
"""

import logging
from unittest.mock import Mock, MagicMock
from netwalker.ipv4_prefix.collector import (
    VRFDiscovery,
    RoutingCollector,
    BGPCollector,
    PrefixCollector
)
from netwalker.ipv4_prefix.data_models import IPv4PrefixConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_vrf_discovery():
    """Test VRF discovery component."""
    logger.info("Testing VRF Discovery...")
    
    vrf_discovery = VRFDiscovery()
    
    # Mock connection
    mock_conn = Mock()
    
    # Test 1: IOS device with VRFs
    mock_conn.send_command.return_value = """
  Name                             Default RD            Interfaces
  MGMT                             <not set>             
  WAN                              65000:100             Gi0/0/1
  GUEST                            65000:200             Gi0/0/2
"""
    vrfs = vrf_discovery.discover_vrfs(mock_conn, 'ios')
    assert len(vrfs) == 3, f"Expected 3 VRFs, got {len(vrfs)}"
    assert 'MGMT' in vrfs, "MGMT VRF not found"
    assert 'WAN' in vrfs, "WAN VRF not found"
    assert 'GUEST' in vrfs, "GUEST VRF not found"
    logger.info("  [OK] IOS VRF discovery")
    
    # Test 2: NX-OS device with VRFs
    mock_conn.send_command.return_value = """
  VRF-Name                           VRF-ID State   Reason
  MGMT                                    2 Up      --
  WAN                                     3 Up      --
"""
    vrfs = vrf_discovery.discover_vrfs(mock_conn, 'nxos')
    assert len(vrfs) == 2, f"Expected 2 VRFs, got {len(vrfs)}"
    assert 'MGMT' in vrfs, "MGMT VRF not found"
    assert 'WAN' in vrfs, "WAN VRF not found"
    logger.info("  [OK] NX-OS VRF discovery")
    
    # Test 3: Device with no VRFs
    mock_conn.send_command.return_value = """
  Name                             Default RD            Interfaces
"""
    vrfs = vrf_discovery.discover_vrfs(mock_conn, 'ios')
    assert len(vrfs) == 0, f"Expected 0 VRFs, got {len(vrfs)}"
    logger.info("  [OK] No VRFs configured")
    
    # Test 4: VRF discovery failure (graceful handling)
    mock_conn.send_command.side_effect = Exception("Connection timeout")
    vrfs = vrf_discovery.discover_vrfs(mock_conn, 'ios')
    assert len(vrfs) == 0, f"Expected 0 VRFs on failure, got {len(vrfs)}"
    logger.info("  [OK] VRF discovery error handling")
    
    logger.info("VRF Discovery: PASSED\n")


def test_routing_collector():
    """Test routing table collection component."""
    logger.info("Testing Routing Collector...")
    
    routing_collector = RoutingCollector()
    
    # Mock connection
    mock_conn = Mock()
    
    # Test 1: Global routes collection
    mock_conn.send_command.return_value = "C    192.168.1.0/24 is directly connected, GigabitEthernet0/0"
    output = routing_collector.collect_global_routes(mock_conn)
    assert output, "Global routes output is empty"
    assert "192.168.1.0/24" in output, "Expected prefix not in output"
    logger.info("  [OK] Global routes collection")
    
    # Test 2: Global connected routes collection
    mock_conn.send_command.return_value = "C    10.0.0.0/8 is directly connected, Loopback0"
    output = routing_collector.collect_global_connected(mock_conn)
    assert output, "Global connected output is empty"
    assert "10.0.0.0/8" in output, "Expected prefix not in output"
    logger.info("  [OK] Global connected routes collection")
    
    # Test 3: VRF routes collection
    mock_conn.send_command.return_value = "B    172.16.0.0/12 [20/0] via 10.1.1.1"
    output = routing_collector.collect_vrf_routes(mock_conn, "WAN")
    assert output, "VRF routes output is empty"
    assert "172.16.0.0/12" in output, "Expected prefix not in output"
    logger.info("  [OK] VRF routes collection")
    
    # Test 4: VRF connected routes collection
    mock_conn.send_command.return_value = "C    192.168.100.0/24 is directly connected, Vlan100"
    output = routing_collector.collect_vrf_connected(mock_conn, "GUEST")
    assert output, "VRF connected output is empty"
    assert "192.168.100.0/24" in output, "Expected prefix not in output"
    logger.info("  [OK] VRF connected routes collection")
    
    # Test 5: VRF name with spaces (sanitization)
    mock_conn.send_command.return_value = "C    10.10.0.0/16 is directly connected, Vlan10"
    output = routing_collector.collect_vrf_routes(mock_conn, "Guest Network")
    assert output, "VRF with spaces output is empty"
    # Verify the command was called with quoted VRF name
    call_args = mock_conn.send_command.call_args[0][0]
    assert '"Guest Network"' in call_args, "VRF name not properly quoted"
    logger.info("  [OK] VRF name sanitization")
    
    # Test 6: Command failure (graceful handling)
    mock_conn.send_command.side_effect = Exception("Command timeout")
    output = routing_collector.collect_global_routes(mock_conn)
    assert output == "", "Expected empty string on failure"
    logger.info("  [OK] Routing collector error handling")
    
    logger.info("Routing Collector: PASSED\n")


def test_bgp_collector():
    """Test BGP collection component."""
    logger.info("Testing BGP Collector...")
    
    bgp_collector = BGPCollector()
    
    # Mock connection
    mock_conn = Mock()
    
    # Test 1: Global BGP collection (BGP configured)
    mock_conn.send_command.return_value = """
BGP table version is 42, local router ID is 10.0.0.1
     Network          Next Hop            Metric LocPrf Weight Path
 *>  10.0.0.0/8       0.0.0.0                  0         32768 i
"""
    output = bgp_collector.collect_global_bgp(mock_conn)
    assert output is not None, "BGP output should not be None"
    assert "10.0.0.0/8" in output, "Expected prefix not in output"
    logger.info("  [OK] Global BGP collection")
    
    # Test 2: Global BGP collection (BGP not configured)
    mock_conn.send_command.return_value = "% BGP not active"
    output = bgp_collector.collect_global_bgp(mock_conn)
    assert output is None, "BGP output should be None when not configured"
    logger.info("  [OK] BGP not configured (graceful degradation)")
    
    # Test 3: VRF BGP collection (IOS/IOS-XE)
    mock_conn.send_command.return_value = """
BGP table version is 10, local router ID is 10.1.1.1
     Network          Next Hop            Metric LocPrf Weight Path
 *>  172.16.0.0/12    10.1.1.2                 0             0 65001 i
"""
    output = bgp_collector.collect_vrf_bgp(mock_conn, "WAN", "ios")
    assert output is not None, "VRF BGP output should not be None"
    assert "172.16.0.0/12" in output, "Expected prefix not in output"
    # Verify correct command was used
    call_args = mock_conn.send_command.call_args[0][0]
    assert "vpnv4" in call_args, "IOS should use 'vpnv4' command"
    logger.info("  [OK] VRF BGP collection (IOS)")
    
    # Test 4: VRF BGP collection (NX-OS)
    mock_conn.send_command.return_value = """
BGP routing table information for VRF WAN
     Network          Next Hop            Metric LocPrf Weight Path
 *>  192.168.0.0/16   10.2.2.2                 0             0 65002 i
"""
    output = bgp_collector.collect_vrf_bgp(mock_conn, "WAN", "nxos")
    assert output is not None, "VRF BGP output should not be None"
    assert "192.168.0.0/16" in output, "Expected prefix not in output"
    # Verify correct command was used
    call_args = mock_conn.send_command.call_args[0][0]
    assert "vpnv4" not in call_args, "NX-OS should not use 'vpnv4' command"
    logger.info("  [OK] VRF BGP collection (NX-OS)")
    
    # Test 5: BGP collection failure (graceful handling)
    mock_conn.send_command.side_effect = Exception("Connection lost")
    output = bgp_collector.collect_global_bgp(mock_conn)
    assert output is None, "BGP output should be None on failure"
    logger.info("  [OK] BGP collector error handling")
    
    logger.info("BGP Collector: PASSED\n")


def test_pagination_control():
    """Test pagination control."""
    logger.info("Testing Pagination Control...")
    
    # Create mock config
    config = IPv4PrefixConfig(
        collect_global_table=True,
        collect_per_vrf=False,
        collect_bgp=False,
        output_directory="./reports",
        create_summary_file=False,
        enable_database_storage=False,
        track_summarization=False,
        concurrent_devices=1,
        command_timeout=30
    )
    
    # Create mock connection manager and credentials
    mock_conn_mgr = Mock()
    mock_creds = Mock()
    
    collector = PrefixCollector(config, mock_conn_mgr, mock_creds)
    
    # Mock connection
    mock_conn = Mock()
    
    # Test 1: Successful pagination disable
    mock_conn.send_command.return_value = ""
    result = collector._disable_pagination(mock_conn)
    assert result is True, "Pagination disable should return True on success"
    mock_conn.send_command.assert_called_with("terminal length 0")
    logger.info("  [OK] Pagination disabled successfully")
    
    # Test 2: Pagination disable failure (graceful handling)
    mock_conn.send_command.side_effect = Exception("Command failed")
    result = collector._disable_pagination(mock_conn)
    assert result is False, "Pagination disable should return False on failure"
    logger.info("  [OK] Pagination error handling")
    
    logger.info("Pagination Control: PASSED\n")


def test_prefix_collector_integration():
    """Test PrefixCollector integration."""
    logger.info("Testing PrefixCollector Integration...")
    
    # Create mock config
    config = IPv4PrefixConfig(
        collect_global_table=True,
        collect_per_vrf=True,
        collect_bgp=True,
        output_directory="./reports",
        create_summary_file=False,
        enable_database_storage=False,
        track_summarization=False,
        concurrent_devices=1,
        command_timeout=30
    )
    
    # Create mock connection manager
    mock_conn_mgr = Mock()
    mock_conn = Mock()
    mock_conn_mgr.connect_device.return_value = (mock_conn, None)
    mock_conn_mgr.close_connection.return_value = None
    
    # Create mock credentials
    mock_creds = Mock()
    
    # Create collector
    collector = PrefixCollector(config, mock_conn_mgr, mock_creds)
    
    # Create mock device
    mock_device = Mock()
    mock_device.hostname = "test-router-01"
    mock_device.platform = "ios"
    mock_device.ip_address = "10.0.0.1"
    
    # Setup mock responses
    mock_conn.send_command.side_effect = [
        "",  # terminal length 0
        "  Name                             Default RD\n  WAN                              65000:100",  # show vrf
        "C    192.168.1.0/24 is directly connected",  # show ip route
        "C    10.0.0.0/8 is directly connected",  # show ip route connected
        "BGP table version is 42\n *>  172.16.0.0/12",  # show ip bgp
        "B    192.168.100.0/24 [20/0] via 10.1.1.1",  # show ip route vrf WAN
        "C    10.10.0.0/16 is directly connected",  # show ip route vrf WAN connected
        "BGP table version is 10\n *>  10.20.0.0/16",  # show ip bgp vpnv4 vrf WAN
    ]
    
    # Test: Collect from device
    result = collector.collect_device(mock_device)
    
    assert result.success is True, "Collection should succeed"
    assert result.device == "test-router-01", "Device name mismatch"
    assert result.platform == "ios", "Platform mismatch"
    assert len(result.vrfs) == 1, f"Expected 1 VRF, got {len(result.vrfs)}"
    assert "WAN" in result.vrfs, "WAN VRF not found"
    assert len(result.raw_outputs) > 0, "No command outputs collected"
    assert result.error is None, f"Unexpected error: {result.error}"
    
    # Verify expected commands were collected
    assert 'show ip route' in result.raw_outputs, "Global routes not collected"
    assert 'show ip route connected' in result.raw_outputs, "Global connected not collected"
    assert 'show ip bgp' in result.raw_outputs, "Global BGP not collected"
    assert 'show ip route vrf WAN' in result.raw_outputs, "VRF routes not collected"
    assert 'show ip route vrf WAN connected' in result.raw_outputs, "VRF connected not collected"
    assert 'show ip bgp vpnv4 vrf WAN' in result.raw_outputs, "VRF BGP not collected"
    
    logger.info("  [OK] PrefixCollector integration")
    logger.info("PrefixCollector Integration: PASSED\n")


def main():
    """Run all checkpoint tests."""
    logger.info("=" * 70)
    logger.info("Task 7 Checkpoint: Collection Components Verification")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        test_vrf_discovery()
        test_routing_collector()
        test_bgp_collector()
        test_pagination_control()
        test_prefix_collector_integration()
        
        logger.info("=" * 70)
        logger.info("ALL TESTS PASSED")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Collection components are working correctly:")
        logger.info("  + VRF Discovery: Discovers VRFs on IOS/IOS-XE/NX-OS devices")
        logger.info("  + Routing Collector: Collects global and per-VRF routing tables")
        logger.info("  + BGP Collector: Collects BGP prefixes with graceful degradation")
        logger.info("  + Pagination Control: Disables pagination before collection")
        logger.info("  + PrefixCollector: Orchestrates complete collection workflow")
        logger.info("")
        logger.info("Ready to proceed to Task 8: Implement prefix parsing")
        
        return True
        
    except AssertionError as e:
        logger.error("=" * 70)
        logger.error("TEST FAILED")
        logger.error("=" * 70)
        logger.error(f"Assertion Error: {str(e)}")
        return False
    except Exception as e:
        logger.error("=" * 70)
        logger.error("TEST ERROR")
        logger.error("=" * 70)
        logger.error(f"Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
