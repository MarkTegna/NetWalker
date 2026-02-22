"""
Task 29: Final Checkpoint - Complete Feature Validation

This test validates the complete IPv4 Prefix Inventory Module implementation
by verifying all components exist, are properly integrated, and function correctly.

Requirements validated: All requirements from the spec
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_module_structure():
    """Verify all required modules and classes exist"""
    print("\n" + "="*70)
    print("TEST 1: Module Structure Validation")
    print("="*70)
    
    # Test data models
    from netwalker.ipv4_prefix.data_models import (
        IPv4PrefixConfig,
        RawPrefix,
        ParsedPrefix,
        NormalizedPrefix,
        DeduplicatedPrefix,
        SummarizationRelationship,
        CollectionException,
        DeviceCollectionResult,
        InventoryResult
    )
    print("[OK] All data models imported successfully")
    
    # Test collector components
    from netwalker.ipv4_prefix.collector import (
        VRFDiscovery,
        RoutingCollector,
        BGPCollector,
        PrefixCollector
    )
    print("[OK] All collector components imported successfully")
    
    # Test parser components
    from netwalker.ipv4_prefix.parser import (
        PrefixExtractor,
        RoutingTableParser,
        BGPParser,
        CommandOutputParser
    )
    print("[OK] All parser components imported successfully")
    
    # Test normalizer components
    from netwalker.ipv4_prefix.normalizer import (
        PrefixNormalizer,
        AmbiguityResolver,
        PrefixDeduplicator
    )
    print("[OK] All normalizer components imported successfully")
    
    # Test summarization components
    from netwalker.ipv4_prefix.summarization import SummarizationAnalyzer
    print("[OK] Summarization analyzer imported successfully")
    
    # Test exporter components
    from netwalker.ipv4_prefix.exporter import (
        CSVExporter,
        ExcelExporter,
        DatabaseExporter
    )
    print("[OK] All exporter components imported successfully")
    
    # Test main orchestrator
    from netwalker.ipv4_prefix import IPv4PrefixInventory
    print("[OK] Main orchestrator imported successfully")
    
    print("\n[PASS] Module structure validation complete")
    return True


def test_data_model_instantiation():
    """Verify data models can be instantiated with correct fields"""
    print("\n" + "="*70)
    print("TEST 2: Data Model Instantiation")
    print("="*70)
    
    from netwalker.ipv4_prefix.data_models import (
        IPv4PrefixConfig,
        ParsedPrefix,
        NormalizedPrefix,
        DeduplicatedPrefix,
        SummarizationRelationship
    )
    from datetime import datetime
    
    # Test IPv4PrefixConfig
    config = IPv4PrefixConfig(
        collect_global_table=True,
        collect_per_vrf=True,
        collect_bgp=True,
        output_directory="./reports",
        create_summary_file=True,
        enable_database_storage=False,
        track_summarization=True,
        concurrent_devices=5,
        command_timeout=30
    )
    assert config.collect_global_table == True
    print("[OK] IPv4PrefixConfig instantiated correctly")
    
    # Test ParsedPrefix
    parsed = ParsedPrefix(
        device="router1",
        platform="ios",
        vrf="global",
        prefix_str="192.168.1.0/24",
        source="rib",
        protocol="C",
        raw_line="C    192.168.1.0/24 is directly connected, GigabitEthernet0/0",
        is_ambiguous=False,
        timestamp=datetime.now()
    )
    assert parsed.device == "router1"
    assert parsed.vrf == "global"
    print("[OK] ParsedPrefix instantiated correctly")
    
    # Test NormalizedPrefix
    normalized = NormalizedPrefix(
        device="router1",
        platform="ios",
        vrf="global",
        prefix="192.168.1.0/24",
        source="rib",
        protocol="C",
        raw_line="C    192.168.1.0/24 is directly connected, GigabitEthernet0/0",
        timestamp=datetime.now()
    )
    assert normalized.prefix == "192.168.1.0/24"
    print("[OK] NormalizedPrefix instantiated correctly")
    
    # Test DeduplicatedPrefix
    dedup = DeduplicatedPrefix(
        vrf="global",
        prefix="192.168.1.0/24",
        device_count=2,
        device_list=["router1", "router2"]
    )
    assert dedup.device_count == 2
    assert len(dedup.device_list) == 2
    print("[OK] DeduplicatedPrefix instantiated correctly")
    
    # Test SummarizationRelationship
    summ = SummarizationRelationship(
        summary_prefix="192.168.0.0/16",
        component_prefix="192.168.1.0/24",
        device="router1",
        vrf="global"
    )
    assert summ.summary_prefix == "192.168.0.0/16"
    assert summ.component_prefix == "192.168.1.0/24"
    print("[OK] SummarizationRelationship instantiated correctly")
    
    print("\n[PASS] Data model instantiation complete")
    return True


def test_parser_functionality():
    """Verify parser can extract prefixes from sample outputs"""
    print("\n" + "="*70)
    print("TEST 3: Parser Functionality")
    print("="*70)
    
    from netwalker.ipv4_prefix.parser import PrefixExtractor
    
    extractor = PrefixExtractor()
    
    # Test CIDR format extraction
    line1 = "C    192.168.1.0/24 is directly connected, GigabitEthernet0/0"
    result1 = extractor.extract_from_route_line(line1)
    assert result1 is not None
    assert "192.168.1.0" in result1.prefix_str
    print("[OK] CIDR format extraction works")
    
    # Test mask format extraction
    line2 = "B    10.0.0.0 255.255.255.0 [20/0] via 10.1.1.1"
    result2 = extractor.extract_from_route_line(line2)
    assert result2 is not None
    assert "10.0.0.0" in result2.prefix_str
    print("[OK] Mask format extraction works")
    
    # Test local route extraction
    line3 = "L    10.0.0.1/32 is directly connected, Loopback0"
    result3 = extractor.extract_from_route_line(line3)
    assert result3 is not None
    assert "/32" in result3.prefix_str
    print("[OK] Local route extraction works")
    
    # Test BGP prefix extraction
    bgp_line = "*> 172.16.0.0/16    10.1.1.1                 0             0 65001 i"
    result4 = extractor.extract_from_bgp_line(bgp_line)
    assert result4 is not None
    assert "172.16.0.0" in result4.prefix_str
    print("[OK] BGP prefix extraction works")
    
    print("\n[PASS] Parser functionality validation complete")
    return True


def test_normalizer_functionality():
    """Verify normalizer can convert prefixes to CIDR notation"""
    print("\n" + "="*70)
    print("TEST 4: Normalizer Functionality")
    print("="*70)
    
    from netwalker.ipv4_prefix.normalizer import PrefixNormalizer
    
    normalizer = PrefixNormalizer()
    
    # Test CIDR validation
    cidr1 = normalizer.normalize("192.168.1.0/24")
    assert cidr1 == "192.168.1.0/24"
    print("[OK] CIDR validation works")
    
    # Test mask to CIDR conversion
    cidr2 = normalizer.mask_to_cidr("10.0.0.0", "255.255.255.0")
    assert cidr2 == "10.0.0.0/24"
    print("[OK] Mask to CIDR conversion works")
    
    # Test /32 host route
    cidr3 = normalizer.normalize("10.0.0.1/32")
    assert cidr3 == "10.0.0.1/32"
    print("[OK] Host route normalization works")
    
    # Test invalid format handling
    invalid = normalizer.normalize("999.999.999.999/32")
    assert invalid is None
    print("[OK] Invalid format handling works")
    
    print("\n[PASS] Normalizer functionality validation complete")
    return True


def test_deduplicator_functionality():
    """Verify deduplicator removes duplicates correctly"""
    print("\n" + "="*70)
    print("TEST 5: Deduplicator Functionality")
    print("="*70)
    
    from netwalker.ipv4_prefix.normalizer import PrefixDeduplicator
    from netwalker.ipv4_prefix.data_models import NormalizedPrefix
    from datetime import datetime
    
    deduplicator = PrefixDeduplicator()
    
    # Create test prefixes with duplicates
    prefixes = [
        NormalizedPrefix("router1", "ios", "global", "192.168.1.0/24", "rib", "C", "", datetime.now()),
        NormalizedPrefix("router1", "ios", "global", "192.168.1.0/24", "rib", "C", "", datetime.now()),  # Duplicate
        NormalizedPrefix("router2", "ios", "global", "192.168.1.0/24", "rib", "C", "", datetime.now()),  # Different device
        NormalizedPrefix("router1", "ios", "VRF_A", "192.168.1.0/24", "rib", "C", "", datetime.now()),  # Different VRF
    ]
    
    # Test device-level deduplication
    dedup_device = deduplicator.deduplicate_by_device(prefixes)
    assert len(dedup_device) == 3  # Should remove 1 duplicate
    print(f"[OK] Device-level deduplication works (3 unique from 4 total)")
    
    # Test VRF-level aggregation
    dedup_vrf = deduplicator.deduplicate_by_vrf(dedup_device)
    assert len(dedup_vrf) == 2  # 2 unique (vrf, prefix) combinations
    print(f"[OK] VRF-level aggregation works (2 unique VRF/prefix combinations)")
    
    # Verify device list aggregation
    global_prefix = [d for d in dedup_vrf if d.vrf == "global"][0]
    assert global_prefix.device_count == 2
    assert "router1" in global_prefix.device_list
    assert "router2" in global_prefix.device_list
    print("[OK] Device list aggregation works")
    
    print("\n[PASS] Deduplicator functionality validation complete")
    return True


def test_summarization_analyzer():
    """Verify summarization analyzer detects relationships"""
    print("\n" + "="*70)
    print("TEST 6: Summarization Analyzer")
    print("="*70)
    
    from netwalker.ipv4_prefix.summarization import SummarizationAnalyzer
    from netwalker.ipv4_prefix.data_models import NormalizedPrefix
    from datetime import datetime
    
    analyzer = SummarizationAnalyzer()
    
    # Test is_component_of
    assert analyzer.is_component_of("192.168.1.0/24", "192.168.0.0/16") == True
    assert analyzer.is_component_of("192.168.1.0/24", "10.0.0.0/8") == False
    print("[OK] Component detection works")
    
    # Test find_components
    prefixes = [
        NormalizedPrefix("router1", "ios", "global", "192.168.0.0/16", "rib", "B", "", datetime.now()),
        NormalizedPrefix("router1", "ios", "global", "192.168.1.0/24", "rib", "C", "", datetime.now()),
        NormalizedPrefix("router1", "ios", "global", "192.168.2.0/24", "rib", "C", "", datetime.now()),
        NormalizedPrefix("router1", "ios", "global", "10.0.0.0/24", "rib", "C", "", datetime.now()),
    ]
    
    components = analyzer.find_components("192.168.0.0/16", prefixes)
    assert len(components) == 2  # Should find 192.168.1.0/24 and 192.168.2.0/24
    print(f"[OK] Component finding works (found {len(components)} components)")
    
    # Test analyze_summarization
    relationships = analyzer.analyze_summarization(prefixes)
    assert len(relationships) > 0
    print(f"[OK] Summarization analysis works (found {len(relationships)} relationships)")
    
    print("\n[PASS] Summarization analyzer validation complete")
    return True


def test_exporter_functionality():
    """Verify exporters can create output files"""
    print("\n" + "="*70)
    print("TEST 7: Exporter Functionality")
    print("="*70)
    
    from netwalker.ipv4_prefix.exporter import CSVExporter
    from netwalker.ipv4_prefix.data_models import NormalizedPrefix, DeduplicatedPrefix, CollectionException
    from datetime import datetime
    import tempfile
    import os
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        exporter = CSVExporter()
        
        # Test prefix export
        prefixes = [
            NormalizedPrefix("router1", "ios", "global", "192.168.1.0/24", "rib", "C", "", datetime.now()),
            NormalizedPrefix("router2", "ios", "global", "10.0.0.0/24", "rib", "B", "", datetime.now()),
        ]
        
        csv_file = exporter.export_prefixes(prefixes, tmpdir)
        assert os.path.exists(csv_file)
        print(f"[OK] Prefix CSV export works: {os.path.basename(csv_file)}")
        
        # Test deduplicated export
        dedup_prefixes = [
            DeduplicatedPrefix("global", "192.168.1.0/24", 2, ["router1", "router2"]),
        ]
        
        dedup_file = exporter.export_deduplicated(dedup_prefixes, tmpdir)
        assert os.path.exists(dedup_file)
        print(f"[OK] Deduplicated CSV export works: {os.path.basename(dedup_file)}")
        
        # Test exceptions export
        exceptions = [
            CollectionException("router1", "show ip bgp", "command_failed", None, "BGP not configured", datetime.now()),
        ]
        
        exc_file = exporter.export_exceptions(exceptions, tmpdir)
        assert os.path.exists(exc_file)
        print(f"[OK] Exceptions CSV export works: {os.path.basename(exc_file)}")
    
    print("\n[PASS] Exporter functionality validation complete")
    return True


def test_configuration_integration():
    """Verify configuration can be loaded"""
    print("\n" + "="*70)
    print("TEST 8: Configuration Integration")
    print("="*70)
    
    from netwalker.ipv4_prefix.data_models import IPv4PrefixConfig
    
    # Test default configuration
    config = IPv4PrefixConfig(
        collect_global_table=True,
        collect_per_vrf=True,
        collect_bgp=True,
        output_directory="./reports",
        create_summary_file=True,
        enable_database_storage=False,
        track_summarization=True,
        concurrent_devices=5,
        command_timeout=30
    )
    
    assert config.collect_global_table == True
    assert config.collect_per_vrf == True
    assert config.collect_bgp == True
    assert config.concurrent_devices == 5
    print("[OK] Configuration loading works")
    
    print("\n[PASS] Configuration integration validation complete")
    return True


def test_end_to_end_workflow():
    """Verify end-to-end workflow with mock data"""
    print("\n" + "="*70)
    print("TEST 9: End-to-End Workflow")
    print("="*70)
    
    from netwalker.ipv4_prefix.parser import PrefixExtractor, RoutingTableParser
    from netwalker.ipv4_prefix.normalizer import PrefixNormalizer, PrefixDeduplicator
    from netwalker.ipv4_prefix.summarization import SummarizationAnalyzer
    from datetime import datetime
    
    # Sample routing table output
    sample_output = """
C    192.168.1.0/24 is directly connected, GigabitEthernet0/0
L    192.168.1.1/32 is directly connected, GigabitEthernet0/0
B    10.0.0.0 255.255.255.0 [20/0] via 10.1.1.1
C    172.16.0.0/16 is directly connected, GigabitEthernet0/1
    """
    
    # Step 1: Parse
    parser = RoutingTableParser()
    parsed_prefixes = parser.parse(sample_output, "router1", "ios", "global")
    assert len(parsed_prefixes) > 0
    print(f"[OK] Step 1: Parsed {len(parsed_prefixes)} prefixes")
    
    # Step 2: Normalize
    normalizer = PrefixNormalizer()
    normalized_prefixes = []
    for p in parsed_prefixes:
        if "/" in p.prefix_str:
            cidr = normalizer.normalize(p.prefix_str)
        else:
            # Handle mask format
            parts = p.prefix_str.split()
            if len(parts) == 2:
                cidr = normalizer.mask_to_cidr(parts[0], parts[1])
            else:
                cidr = normalizer.normalize(p.prefix_str)
        
        if cidr:
            from netwalker.ipv4_prefix.data_models import NormalizedPrefix
            normalized_prefixes.append(NormalizedPrefix(
                p.device, p.platform, p.vrf, cidr, p.source, p.protocol, p.raw_line, p.timestamp
            ))
    
    assert len(normalized_prefixes) > 0
    print(f"[OK] Step 2: Normalized {len(normalized_prefixes)} prefixes")
    
    # Step 3: Deduplicate
    deduplicator = PrefixDeduplicator()
    dedup_device = deduplicator.deduplicate_by_device(normalized_prefixes)
    dedup_vrf = deduplicator.deduplicate_by_vrf(dedup_device)
    print(f"[OK] Step 3: Deduplicated to {len(dedup_vrf)} unique prefixes")
    
    # Step 4: Analyze summarization
    analyzer = SummarizationAnalyzer()
    relationships = analyzer.analyze_summarization(normalized_prefixes)
    print(f"[OK] Step 4: Found {len(relationships)} summarization relationships")
    
    print("\n[PASS] End-to-end workflow validation complete")
    return True


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("IPv4 PREFIX INVENTORY MODULE - FINAL VALIDATION (TASK 29)")
    print("="*70)
    print("Validating complete feature implementation...")
    
    tests = [
        ("Module Structure", test_module_structure),
        ("Data Model Instantiation", test_data_model_instantiation),
        ("Parser Functionality", test_parser_functionality),
        ("Normalizer Functionality", test_normalizer_functionality),
        ("Deduplicator Functionality", test_deduplicator_functionality),
        ("Summarization Analyzer", test_summarization_analyzer),
        ("Exporter Functionality", test_exporter_functionality),
        ("Configuration Integration", test_configuration_integration),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n[FAIL] {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("FINAL VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] All validation tests passed!")
        print("The IPv4 Prefix Inventory Module is complete and ready for use.")
        return True
    else:
        print(f"\n[WARNING] {failed} test(s) failed. Review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
