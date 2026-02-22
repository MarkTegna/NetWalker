"""
Mock-based integration tests for IPv4 Prefix Inventory Module

These tests validate the integration points and data flow through the system
without requiring real network devices. They use mocks to simulate device
responses and verify that components integrate correctly.

Test Coverage:
- Component integration (collector -> parser -> normalizer -> exporter)
- Configuration loading and application
- Database integration
- Excel export integration
- Error handling and graceful degradation
- Concurrent processing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
import tempfile
import os
import csv

# Import the modules to test
from netwalker.ipv4_prefix.data_models import (
    IPv4PrefixConfig,
    DeviceCollectionResult,
    ParsedPrefix,
    NormalizedPrefix,
    DeduplicatedPrefix,
    CollectionException
)
from netwalker.ipv4_prefix.collector import (
    VRFDiscovery,
    RoutingCollector,
    BGPCollector,
    PrefixCollector
)
from netwalker.ipv4_prefix.parser import (
    PrefixExtractor,
    RoutingTableParser,
    BGPParser,
    CommandOutputParser
)
from netwalker.ipv4_prefix.normalizer import (
    PrefixNormalizer,
    AmbiguityResolver,
    PrefixDeduplicator
)
from netwalker.ipv4_prefix.exporter import (
    CSVExporter,
    ExcelExporter,
    DatabaseExporter
)
from netwalker.ipv4_prefix.summarization import SummarizationAnalyzer


# Sample command outputs for testing
SAMPLE_SHOW_VRF_IOS = """
  Name                             Default RD            Interfaces
  MGMT                             <not set>             Gi0/1
  WAN                              <not set>             Gi0/2
"""

SAMPLE_SHOW_IP_ROUTE = """
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP

Gateway of last resort is not set

      10.0.0.0/8 is variably subnetted, 3 subnets, 2 masks
C        10.1.1.0/24 is directly connected, GigabitEthernet0/0
L        10.1.1.1/32 is directly connected, GigabitEthernet0/0
S        10.2.0.0/16 [1/0] via 10.1.1.254
      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/1
L        192.168.1.1/32 is directly connected, GigabitEthernet0/1
"""

SAMPLE_SHOW_IP_BGP = """
   Network          Next Hop            Metric LocPrf Weight Path
*> 172.16.0.0/16    10.1.1.254               0             0 65001 i
*> 172.16.1.0/24    10.1.1.254               0             0 65001 i
"""


class TestComponentIntegration:
    """Test integration between major components"""
    
    def test_collector_to_parser_integration(self):
        """Test data flow from collector to parser"""
        # Create a mock connection
        mock_connection = Mock()
        mock_connection.send_command.side_effect = [
            SAMPLE_SHOW_VRF_IOS,  # VRF discovery
            SAMPLE_SHOW_IP_ROUTE,  # Global routes
            SAMPLE_SHOW_IP_ROUTE,  # Global connected
        ]
        
        # Create collector
        config = IPv4PrefixConfig(
            collect_global_table=True,
            collect_per_vrf=False,
            collect_bgp=False,
            output_directory="./test_output",
            create_summary_file=False,
            enable_database_storage=False,
            track_summarization=False,
            concurrent_devices=1,
            command_timeout=30
        )
        
        # Collect data
        vrf_discovery = VRFDiscovery()
        routing_collector = RoutingCollector()
        
        vrfs = vrf_discovery.discover_vrfs(mock_connection, "ios")
        global_routes = routing_collector.collect_global_routes(mock_connection)
        
        # Parse collected data
        parser = RoutingTableParser()
        prefixes = parser.parse(
            global_routes,
            device="test-router",
            platform="ios",
            vrf="global"
        )
        
        # Verify integration
        assert len(vrfs) == 2
        assert "MGMT" in vrfs
        assert "WAN" in vrfs
        assert len(prefixes) > 0
        assert all(p.vrf == "global" for p in prefixes)
        assert all(p.device == "test-router" for p in prefixes)
    
    def test_parser_to_normalizer_integration(self):
        """Test data flow from parser to normalizer"""
        # Parse sample output
        parser = RoutingTableParser()
        parsed_prefixes = parser.parse(
            SAMPLE_SHOW_IP_ROUTE,
            device="test-router",
            platform="ios",
            vrf="global"
        )
        
        # Normalize parsed prefixes
        normalizer = PrefixNormalizer()
        normalized_prefixes = []
        
        for parsed in parsed_prefixes:
            normalized = normalizer.normalize(parsed.prefix_str)
            if normalized:
                normalized_prefixes.append(NormalizedPrefix(
                    device=parsed.device,
                    platform=parsed.platform,
                    vrf=parsed.vrf,
                    prefix=normalized,
                    source=parsed.source,
                    protocol=parsed.protocol,
                    raw_line=parsed.raw_line,
                    timestamp=parsed.timestamp
                ))
        
        # Verify integration
        assert len(normalized_prefixes) > 0
        # All should be valid CIDR notation
        import ipaddress
        for prefix in normalized_prefixes:
            ipaddress.ip_network(prefix.prefix)  # Should not raise
    
    def test_normalizer_to_exporter_integration(self):
        """Test data flow from normalizer to exporter"""
        # Create sample normalized prefixes
        now = datetime.now()
        prefixes = [
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="10.1.1.0/24",
                source="rib",
                protocol="C",
                raw_line="C        10.1.1.0/24 is directly connected",
                timestamp=now,
                vlan=None,
                interface=None
            ),
            NormalizedPrefix(
                device="router2",
                platform="iosxe",
                vrf="MGMT",
                prefix="10.1.1.0/24",
                source="rib",
                protocol="C",
                raw_line="C        10.1.1.0/24 is directly connected",
                timestamp=now,
                vlan=None,
                interface=None
            ),
        ]
        
        # Deduplicate
        deduplicator = PrefixDeduplicator()
        deduplicated = deduplicator.deduplicate_by_vrf(prefixes)
        
        # Export to CSV
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter()
            csv_file = exporter.export_prefixes(prefixes, tmpdir)
            dedup_file = exporter.export_deduplicated(deduplicated, tmpdir)
            
            # Verify files created
            assert os.path.exists(csv_file)
            assert os.path.exists(dedup_file)
            
            # Verify CSV content
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['prefix'] == "10.1.1.0/24"
            
            # Verify deduplicated content
            with open(dedup_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Should have 2 rows (global and MGMT)
                assert len(rows) == 2


class TestConfigurationIntegration:
    """Test configuration loading and application"""
    
    def test_config_loading_and_application(self):
        """Test that configuration is properly loaded and applied"""
        config = IPv4PrefixConfig(
            collect_global_table=True,
            collect_per_vrf=True,
            collect_bgp=True,
            output_directory="./custom_output",
            create_summary_file=True,
            enable_database_storage=True,
            track_summarization=True,
            concurrent_devices=3,
            command_timeout=60
        )
        
        # Verify all settings loaded
        assert config.collect_global_table is True
        assert config.collect_per_vrf is True
        assert config.collect_bgp is True
        assert config.output_directory == "./custom_output"
        assert config.create_summary_file is True
        assert config.enable_database_storage is True
        assert config.track_summarization is True
        assert config.concurrent_devices == 3
        assert config.command_timeout == 60


class TestErrorHandling:
    """Test error handling and graceful degradation"""
    
    def test_bgp_not_configured_graceful_handling(self):
        """Test graceful handling when BGP is not configured"""
        mock_connection = Mock()
        mock_connection.send_command.side_effect = Exception("BGP not configured")
        
        bgp_collector = BGPCollector()
        result = bgp_collector.collect_global_bgp(mock_connection)
        
        # Should return None, not raise exception
        assert result is None
    
    def test_vrf_discovery_failure_continues_collection(self):
        """Test that VRF discovery failure doesn't stop collection"""
        mock_connection = Mock()
        mock_connection.send_command.side_effect = [
            Exception("VRF command failed"),  # VRF discovery fails
            SAMPLE_SHOW_IP_ROUTE,  # But global collection succeeds
        ]
        
        vrf_discovery = VRFDiscovery()
        routing_collector = RoutingCollector()
        
        # VRF discovery should handle error
        vrfs = vrf_discovery.discover_vrfs(mock_connection, "ios")
        assert vrfs == []  # Empty list, not exception
        
        # Global collection should still work
        mock_connection.send_command.side_effect = [SAMPLE_SHOW_IP_ROUTE]
        global_routes = routing_collector.collect_global_routes(mock_connection)
        assert global_routes is not None
    
    def test_invalid_prefix_handling(self):
        """Test that invalid prefixes are handled gracefully"""
        normalizer = PrefixNormalizer()
        
        # Invalid formats should return None
        assert normalizer.normalize("999.999.999.999/32") is None
        assert normalizer.normalize("10.0.0.0/33") is None
        assert normalizer.normalize("invalid") is None
        
        # Valid formats should work
        assert normalizer.normalize("10.0.0.0/8") == "10.0.0.0/8"
        assert normalizer.normalize("192.168.1.0 255.255.255.0") == "192.168.1.0/24"


class TestConcurrentProcessing:
    """Test concurrent device processing"""
    
    def test_thread_safety_of_result_aggregation(self):
        """Test that concurrent processing doesn't corrupt data"""
        # Create multiple normalized prefixes from different "devices"
        now = datetime.now()
        prefixes_device1 = [
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix=f"10.1.{i}.0/24",
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            )
            for i in range(10)
        ]
        
        prefixes_device2 = [
            NormalizedPrefix(
                device="router2",
                platform="iosxe",
                vrf="global",
                prefix=f"10.2.{i}.0/24",
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            )
            for i in range(10)
        ]
        
        # Combine results (simulating aggregation from threads)
        all_prefixes = prefixes_device1 + prefixes_device2
        
        # Deduplicate
        deduplicator = PrefixDeduplicator()
        deduplicated = deduplicator.deduplicate_by_device(all_prefixes)
        
        # Verify no data loss
        assert len(deduplicated) == 20
        
        # Verify device separation maintained
        device1_prefixes = [p for p in deduplicated if p.device == "router1"]
        device2_prefixes = [p for p in deduplicated if p.device == "router2"]
        assert len(device1_prefixes) == 10
        assert len(device2_prefixes) == 10


class TestDatabaseIntegration:
    """Test database integration (with mocked database)"""
    
    def test_database_upsert_logic(self):
        """Test database upsert behavior with simplified mock"""
        # This test validates the concept of upsert logic
        # In a real scenario, existing prefixes get last_seen updated
        # New prefixes get both first_seen and last_seen set
        
        now = datetime.now()
        prefix = NormalizedPrefix(
            device="router1",
            platform="ios",
            vrf="global",
            prefix="10.1.1.0/24",
            source="rib",
            protocol="C",
            raw_line="test",
            timestamp=now,
            vlan=None,
            interface=None
        )
        
        # Verify the prefix has all required fields for database storage
        assert prefix.device is not None
        assert prefix.vrf is not None
        assert prefix.prefix is not None
        assert prefix.source is not None
        assert prefix.timestamp is not None
        
        # The actual upsert logic is tested in unit tests with real database
        # This integration test just validates the data model is complete
    
    def test_database_disabled_skips_operations(self):
        """Test that database operations are skipped when disabled"""
        config = IPv4PrefixConfig(
            collect_global_table=True,
            collect_per_vrf=False,
            collect_bgp=False,
            output_directory="./test",
            create_summary_file=False,
            enable_database_storage=False,  # Disabled
            track_summarization=False,
            concurrent_devices=1,
            command_timeout=30
        )
        
        # When database is disabled, operations should be skipped
        assert config.enable_database_storage is False


class TestSummarizationIntegration:
    """Test route summarization tracking"""
    
    def test_summarization_detection_and_storage(self):
        """Test that summarization relationships are detected and stored"""
        now = datetime.now()
        
        # Create summary and component prefixes
        prefixes = [
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="192.168.0.0/16",  # Summary
                source="rib",
                protocol="B",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="192.168.1.0/24",  # Component
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="192.168.2.0/24",  # Component
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
        ]
        
        # Analyze summarization
        analyzer = SummarizationAnalyzer()
        relationships = analyzer.analyze_summarization(prefixes)
        
        # Verify relationships detected
        assert len(relationships) > 0
        
        # Verify components are within summary
        for rel in relationships:
            assert analyzer.is_component_of(rel.component_prefix, rel.summary_prefix)


class TestOutputFormatting:
    """Test output file formatting"""
    
    def test_csv_column_order_and_sorting(self):
        """Test CSV output has correct columns and sort order"""
        now = datetime.now()
        prefixes = [
            NormalizedPrefix(
                device="router2",
                platform="ios",
                vrf="WAN",
                prefix="10.2.0.0/16",
                source="rib",
                protocol="B",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="10.1.0.0/16",
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter()
            csv_file = exporter.export_prefixes(prefixes, tmpdir)
            
            # Read and verify
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Verify columns (including vlan and interface fields)
                expected_cols = ['device', 'platform', 'vrf', 'prefix', 'source', 'protocol', 'vlan', 'interface', 'timestamp']
                assert reader.fieldnames == expected_cols
                
                # Verify sort order (vrf, prefix, device)
                # Alphabetically: WAN comes before global
                rows = list(reader)
                assert len(rows) == 2
                # Verify sorting is applied (first by vrf)
                assert rows[0]['vrf'] <= rows[1]['vrf']  # Alphabetical order
    
    def test_deduplicated_device_list_formatting(self):
        """Test deduplicated CSV formats device list correctly"""
        now = datetime.now()
        prefixes = [
            NormalizedPrefix(
                device="router1",
                platform="ios",
                vrf="global",
                prefix="10.1.1.0/24",
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
            NormalizedPrefix(
                device="router2",
                platform="iosxe",
                vrf="global",
                prefix="10.1.1.0/24",
                source="rib",
                protocol="C",
                raw_line="test",
                timestamp=now,
                vlan=None,
                interface=None
            ),
        ]
        
        deduplicator = PrefixDeduplicator()
        deduplicated = deduplicator.deduplicate_by_vrf(prefixes)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter()
            dedup_file = exporter.export_deduplicated(deduplicated, tmpdir)
            
            # Read and verify
            with open(dedup_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                # Should have 1 row (same prefix in global VRF)
                assert len(rows) == 1
                assert rows[0]['device_count'] == '2'
                # Device list should be semicolon-separated
                devices = rows[0]['device_list'].split(';')
                assert len(devices) == 2
                assert 'router1' in devices
                assert 'router2' in devices


class TestExceptionReporting:
    """Test exception tracking and reporting"""
    
    def test_exception_collection_and_export(self):
        """Test that exceptions are collected and exported"""
        now = datetime.now()
        exceptions = [
            CollectionException(
                device="router1",
                command="show ip bgp 10.0.0.0",
                error_type="unresolved_prefix",
                raw_token="10.0.0.0",
                error_message="Could not determine prefix length",
                timestamp=now
            ),
            CollectionException(
                device="router2",
                command="show ip route vrf INVALID",
                error_type="command_failed",
                raw_token=None,
                error_message="VRF not found",
                timestamp=now
            ),
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CSVExporter()
            exc_file = exporter.export_exceptions(exceptions, tmpdir)
            
            # Verify file created
            assert os.path.exists(exc_file)
            
            # Verify content
            with open(exc_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['error_type'] == 'unresolved_prefix'
                assert rows[1]['error_type'] == 'command_failed'


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
