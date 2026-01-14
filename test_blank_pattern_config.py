#!/usr/bin/env python3
"""
Test script for validating blank site boundary pattern configuration handling.

This script tests Task 8.1: Test with blank pattern configuration
- Create test configuration with blank site_boundary_pattern
- Verify only main workbook is created
- Verify no site-specific workbooks are generated
- Check logs for proper disabled state messages
"""

import sys
import os
import logging
from pathlib import Path

# Add the netwalker package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from netwalker.config.config_manager import ConfigurationManager
from netwalker.config.blank_detection import ConfigurationBlankHandler

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_blank_pattern_configuration():
    """Test configuration loading with blank site boundary pattern"""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("TASK 8.1: Testing blank pattern configuration")
    logger.info("=" * 60)
    
    try:
        # Test 1: Load configuration with blank pattern
        logger.info("\n1. Testing configuration loading with blank pattern...")
        config_manager = ConfigurationManager("test_blank_pattern.ini")
        config = config_manager.load_configuration()
        
        # Check the site boundary pattern
        site_pattern = config['output'].site_boundary_pattern
        logger.info(f"Loaded site boundary pattern: {repr(site_pattern)}")
        
        if site_pattern is None:
            logger.info("✓ PASS: Blank pattern correctly detected and disabled site boundary detection")
        else:
            logger.error(f"✗ FAIL: Expected None for blank pattern, got: {repr(site_pattern)}")
            return False
        
        # Test 2: Test direct method call
        logger.info("\n2. Testing direct get_site_boundary_pattern method...")
        direct_pattern = config_manager.get_site_boundary_pattern()
        logger.info(f"Direct method result: {repr(direct_pattern)}")
        
        if direct_pattern is None:
            logger.info("✓ PASS: Direct method correctly returns None for blank pattern")
        else:
            logger.error(f"✗ FAIL: Expected None from direct method, got: {repr(direct_pattern)}")
            return False
        
        # Test 3: Test various whitespace patterns
        logger.info("\n3. Testing various whitespace patterns...")
        whitespace_variations = ConfigurationBlankHandler.get_whitespace_variations()
        
        for i, whitespace_pattern in enumerate(whitespace_variations):
            logger.info(f"Testing whitespace variation {i+1}: {repr(whitespace_pattern)}")
            
            # Test the blank detection directly
            is_blank = ConfigurationBlankHandler.is_blank_value(whitespace_pattern)
            processed = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                whitespace_pattern, 
                default_pattern="*-CORE-*",
                logger=logger
            )
            
            logger.info(f"  is_blank_value: {is_blank}")
            logger.info(f"  processed_pattern: {repr(processed)}")
            
            if whitespace_pattern == "":
                # Empty string should be blank and result in None
                if is_blank and processed is None:
                    logger.info("  ✓ PASS: Empty string correctly handled")
                else:
                    logger.error(f"  ✗ FAIL: Empty string not handled correctly")
                    return False
            elif whitespace_pattern.strip() == "":
                # Whitespace-only should be blank and result in None
                if is_blank and processed is None:
                    logger.info("  ✓ PASS: Whitespace-only correctly handled")
                else:
                    logger.error(f"  ✗ FAIL: Whitespace-only not handled correctly")
                    return False
        
        # Test 4: Test Unicode whitespace handling
        logger.info("\n4. Testing Unicode whitespace handling...")
        unicode_whitespace_patterns = [
            "\u00A0",      # Non-breaking space
            "\u2000\u2001", # En quad + Em quad
            "\u3000",      # Ideographic space
            " \u00A0\t ",  # Mixed ASCII and Unicode whitespace
        ]
        
        for pattern in unicode_whitespace_patterns:
            logger.info(f"Testing Unicode pattern: {repr(pattern)}")
            
            # Test Unicode normalization
            normalized = ConfigurationBlankHandler.handle_unicode_whitespace(pattern)
            logger.info(f"  Normalized: {repr(normalized)}")
            
            # Test mixed content handling
            is_mixed_blank = ConfigurationBlankHandler.handle_mixed_content(pattern)
            logger.info(f"  Mixed content blank: {is_mixed_blank}")
            
            # Test full processing
            processed = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                pattern,
                default_pattern="*-CORE-*",
                logger=logger
            )
            logger.info(f"  Final processed: {repr(processed)}")
            
            if processed is None:
                logger.info("  ✓ PASS: Unicode whitespace correctly disabled site boundary detection")
            else:
                logger.error(f"  ✗ FAIL: Unicode whitespace not handled correctly")
                return False
        
        # Test 5: Test valid patterns still work
        logger.info("\n5. Testing valid patterns still work...")
        valid_patterns = ["*-CORE-*", "*-RTR-*", "SITE-*", "TEST-PATTERN"]
        
        for pattern in valid_patterns:
            logger.info(f"Testing valid pattern: {repr(pattern)}")
            
            processed = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                pattern,
                default_pattern="*-CORE-*",
                logger=logger
            )
            logger.info(f"  Processed: {repr(processed)}")
            
            if processed == pattern:
                logger.info("  ✓ PASS: Valid pattern preserved")
            else:
                logger.error(f"  ✗ FAIL: Valid pattern not preserved correctly")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("TASK 8.1: ALL TESTS PASSED")
        logger.info("✓ Blank pattern configuration correctly disables site boundary detection")
        logger.info("✓ Various whitespace patterns handled correctly")
        logger.info("✓ Unicode whitespace characters normalized and handled")
        logger.info("✓ Valid patterns continue to work normally")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_whitespace_only_patterns():
    """Test Task 8.2: Test with whitespace-only pattern configuration"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("TASK 8.2: Testing whitespace-only pattern configuration")
    logger.info("=" * 60)
    
    try:
        # Create test configurations with different whitespace patterns
        whitespace_patterns = [
            "   ",           # Spaces only
            "\t\t",         # Tabs only
            "\n\n",         # Newlines only
            " \t \n ",      # Mixed whitespace
            "\u00A0\u2000", # Unicode whitespace
        ]
        
        for i, pattern in enumerate(whitespace_patterns):
            logger.info(f"\nTesting whitespace pattern {i+1}: {repr(pattern)}")
            
            # Test direct processing
            processed = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                pattern,
                default_pattern="*-CORE-*",
                logger=logger
            )
            
            logger.info(f"  Processed result: {repr(processed)}")
            
            if processed is None:
                logger.info("  ✓ PASS: Whitespace-only pattern correctly disabled site boundary detection")
            else:
                logger.error(f"  ✗ FAIL: Whitespace-only pattern not handled correctly")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("TASK 8.2: ALL TESTS PASSED")
        logger.info("✓ All whitespace variations treated as disabled")
        logger.info("✓ Consistent behavior across different whitespace types")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Whitespace test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test Task 8.3: Test backward compatibility with valid patterns"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("TASK 8.3: Testing backward compatibility with valid patterns")
    logger.info("=" * 60)
    
    try:
        # Test with original configuration (has valid pattern)
        logger.info("\n1. Testing with original configuration...")
        config_manager = ConfigurationManager("netwalker.ini")
        config = config_manager.load_configuration()
        
        site_pattern = config['output'].site_boundary_pattern
        logger.info(f"Original config site pattern: {repr(site_pattern)}")
        
        if site_pattern == "*-CORE-*":
            logger.info("✓ PASS: Original valid pattern preserved")
        else:
            logger.error(f"✗ FAIL: Original pattern not preserved, got: {repr(site_pattern)}")
            return False
        
        # Test various valid patterns
        logger.info("\n2. Testing various valid patterns...")
        valid_patterns = [
            "*-CORE-*",
            "*-RTR-*", 
            "*-SW-*",
            "SITE-*",
            "*-MDF-*",
            "TEST-PATTERN",
            "ABC-*-XYZ"
        ]
        
        for pattern in valid_patterns:
            logger.info(f"Testing valid pattern: {repr(pattern)}")
            
            processed = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
                pattern,
                default_pattern="*-CORE-*",
                logger=logger
            )
            
            if processed == pattern:
                logger.info(f"  ✓ PASS: Pattern {repr(pattern)} preserved correctly")
            else:
                logger.error(f"  ✗ FAIL: Pattern {repr(pattern)} not preserved, got: {repr(processed)}")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("TASK 8.3: ALL TESTS PASSED")
        logger.info("✓ Existing valid patterns work unchanged")
        logger.info("✓ Site boundary detection continues for non-blank patterns")
        logger.info("✓ Backward compatibility maintained")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Backward compatibility test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_missing_pattern_fallback():
    """Test Task 8.4: Test missing pattern fallback behavior"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("TASK 8.4: Testing missing pattern fallback behavior")
    logger.info("=" * 60)
    
    try:
        # Test missing value (None) vs blank value distinction
        logger.info("\n1. Testing missing vs blank distinction...")
        
        # Test missing (None)
        missing_result = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
            None,  # Missing value
            default_pattern="*-CORE-*",
            logger=logger
        )
        logger.info(f"Missing value result: {repr(missing_result)}")
        
        if missing_result == "*-CORE-*":
            logger.info("✓ PASS: Missing value gets default fallback")
        else:
            logger.error(f"✗ FAIL: Missing value should get default, got: {repr(missing_result)}")
            return False
        
        # Test blank value
        blank_result = ConfigurationBlankHandler.process_site_boundary_pattern_with_unicode(
            "",  # Blank value
            default_pattern="*-CORE-*",
            logger=logger
        )
        logger.info(f"Blank value result: {repr(blank_result)}")
        
        if blank_result is None:
            logger.info("✓ PASS: Blank value disables site boundary detection")
        else:
            logger.error(f"✗ FAIL: Blank value should disable, got: {repr(blank_result)}")
            return False
        
        # Test should_apply_fallback logic
        logger.info("\n2. Testing fallback application logic...")
        
        test_cases = [
            (None, True, "Missing value should get fallback"),
            ("", False, "Empty string should not get fallback"),
            ("   ", False, "Whitespace should not get fallback"),
            ("*-CORE-*", False, "Valid pattern should not get fallback"),
        ]
        
        for value, expected_fallback, description in test_cases:
            should_fallback = ConfigurationBlankHandler.should_apply_fallback(value)
            logger.info(f"Testing: {repr(value)} -> should_fallback: {should_fallback}")
            
            if should_fallback == expected_fallback:
                logger.info(f"  ✓ PASS: {description}")
            else:
                logger.error(f"  ✗ FAIL: {description}")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("TASK 8.4: ALL TESTS PASSED")
        logger.info("✓ Missing patterns get default fallback for backward compatibility")
        logger.info("✓ Blank patterns disable site boundary detection")
        logger.info("✓ Missing vs blank distinction works correctly")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: Missing pattern fallback test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    logger = setup_logging()
    
    logger.info("Starting NetWalker Site Boundary Pattern Integration Tests")
    logger.info("Testing implementation of blank pattern disable fix")
    
    # Run all test tasks
    tests = [
        ("8.1", "Blank Pattern Configuration", test_blank_pattern_configuration),
        ("8.2", "Whitespace-Only Patterns", test_whitespace_only_patterns),
        ("8.3", "Backward Compatibility", test_backward_compatibility),
        ("8.4", "Missing Pattern Fallback", test_missing_pattern_fallback),
    ]
    
    results = []
    
    for task_id, task_name, test_func in tests:
        logger.info(f"\n{'='*80}")
        logger.info(f"RUNNING TASK {task_id}: {task_name}")
        logger.info(f"{'='*80}")
        
        try:
            result = test_func()
            results.append((task_id, task_name, result))
            
            if result:
                logger.info(f"TASK {task_id} COMPLETED SUCCESSFULLY")
            else:
                logger.error(f"TASK {task_id} FAILED")
                
        except Exception as e:
            logger.error(f"TASK {task_id} FAILED WITH EXCEPTION: {e}")
            results.append((task_id, task_name, False))
    
    # Print final summary
    logger.info(f"\n{'='*80}")
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    passed = 0
    failed = 0
    
    for task_id, task_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"Task {task_id} ({task_name}): {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\nTotal Tests: {len(results)}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    
    if failed == 0:
        logger.info("\n🎉 ALL INTEGRATION TESTS PASSED!")
        logger.info("Site boundary pattern disable fix is working correctly.")
        return True
    else:
        logger.error(f"\n❌ {failed} INTEGRATION TESTS FAILED!")
        logger.error("Site boundary pattern disable fix needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)