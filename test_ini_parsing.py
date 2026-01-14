#!/usr/bin/env python3
"""
Test INI file parsing to diagnose max_depth issue.
"""

import sys
import logging
import configparser
from io import StringIO

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

def test_ini_parsing():
    """Test different INI file formats"""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("TESTING INI FILE PARSING")
    logger.info("=" * 80)
    
    # Test case 1: Correct format with newlines
    correct_ini = """[discovery]
# Maximum depth for recursive discovery
max_depth = 99
# Number of concurrent device connections
concurrent_connections = 5
"""
    
    # Test case 2: No newline after value (like user's file)
    broken_ini = """[discovery]
# Maximum depth for recursive discovery
max_depth = 99# Number of concurrent device connections
concurrent_connections = 5
"""
    
    # Test case 3: Comment on same line as value
    inline_comment_ini = """[discovery]
# Maximum depth for recursive discovery
max_depth = 99  # Number of concurrent device connections
concurrent_connections = 5
"""
    
    test_cases = [
        ("Correct format", correct_ini),
        ("No newline after value", broken_ini),
        ("Inline comment", inline_comment_ini)
    ]
    
    for name, ini_content in test_cases:
        logger.info(f"\n{'-' * 60}")
        logger.info(f"Test: {name}")
        logger.info(f"{'-' * 60}")
        
        try:
            config = configparser.ConfigParser()
            config.read_string(ini_content)
            
            if config.has_section('discovery'):
                max_depth = config.getint('discovery', 'max_depth', fallback=1)
                concurrent = config.getint('discovery', 'concurrent_connections', fallback=5)
                
                logger.info(f"  max_depth: {max_depth}")
                logger.info(f"  concurrent_connections: {concurrent}")
                
                if max_depth == 99:
                    logger.info(f"  ✅ Parsed correctly")
                else:
                    logger.error(f"  ❌ PARSING ERROR - expected 99, got {max_depth}")
            else:
                logger.error(f"  ❌ No [discovery] section found")
                
        except Exception as e:
            logger.error(f"  ❌ Exception: {e}")
    
    return True

def test_actual_ini_file():
    """Test the actual netwalker.ini file"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 80)
    logger.info("TESTING ACTUAL netwalker.ini FILE")
    logger.info("=" * 80)
    
    try:
        config = configparser.ConfigParser()
        config.read('netwalker.ini')
        
        if config.has_section('discovery'):
            max_depth = config.getint('discovery', 'max_depth', fallback=1)
            logger.info(f"max_depth from netwalker.ini: {max_depth}")
            
            if max_depth == 99:
                logger.info("✅ netwalker.ini is parsing correctly")
            else:
                logger.error(f"❌ netwalker.ini parsing issue - expected 99, got {max_depth}")
                
                # Show the raw value
                raw_value = config.get('discovery', 'max_depth', fallback='NOT FOUND')
                logger.info(f"Raw value: '{raw_value}'")
                logger.info(f"Raw value repr: {repr(raw_value)}")
        else:
            logger.error("❌ No [discovery] section in netwalker.ini")
            
    except FileNotFoundError:
        logger.warning("netwalker.ini not found in current directory")
    except Exception as e:
        logger.error(f"Error reading netwalker.ini: {e}")
    
    return True

def main():
    """Main test function"""
    logger = setup_logging()
    
    logger.info("NetWalker INI Parsing Investigation")
    
    # Test different INI formats
    test_ini_parsing()
    
    # Test actual file
    test_actual_ini_file()
    
    logger.info("\n" + "=" * 80)
    logger.info("RECOMMENDATION")
    logger.info("=" * 80)
    logger.info("\nIf max_depth is not parsing correctly, ensure your INI file has:")
    logger.info("1. Proper newlines after each value")
    logger.info("2. Comments on separate lines (not inline)")
    logger.info("\nCorrect format:")
    logger.info("  max_depth = 99")
    logger.info("  # Comment on next line")
    logger.info("\nIncorrect format:")
    logger.info("  max_depth = 99# Comment on same line")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)