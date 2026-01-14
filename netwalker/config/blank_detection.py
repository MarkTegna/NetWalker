"""
Configuration Blank Detection Utility for NetWalker

This module provides utilities to distinguish between missing and blank configuration values,
specifically addressing the site boundary pattern configuration bug where blank values
should disable site boundary detection rather than falling back to default patterns.
"""

import logging
from typing import Optional, Any, Tuple


class ConfigurationBlankHandler:
    """
    Utility class for handling blank configuration values correctly.
    
    This class addresses the critical issue where blank site_boundary_pattern values
    are not properly disabling site boundary detection. It provides methods to:
    1. Detect intentionally blank configuration values
    2. Distinguish between missing and blank values
    3. Determine when fallback values should be applied
    """
    
    @staticmethod
    def is_blank_value(value: Any) -> bool:
        """
        Check if a configuration value is intentionally blank.
        
        A value is considered blank if it's a string that contains only whitespace
        characters (spaces, tabs, newlines, etc.) or is an empty string.
        
        Args:
            value: The configuration value to check
            
        Returns:
            bool: True if the value is intentionally blank, False otherwise
            
        Examples:
            >>> ConfigurationBlankHandler.is_blank_value("")
            True
            >>> ConfigurationBlankHandler.is_blank_value("   ")
            True
            >>> ConfigurationBlankHandler.is_blank_value("\t\n  ")
            True
            >>> ConfigurationBlankHandler.is_blank_value("*-CORE-*")
            False
            >>> ConfigurationBlankHandler.is_blank_value(None)
            False
        """
        if value is None:
            return False
        
        if not isinstance(value, str):
            return False
            
        # Check if string contains only whitespace characters
        return value.strip() == ""
    
    @staticmethod
    def is_missing_value(value: Any) -> bool:
        """
        Check if a configuration value is missing entirely.
        
        A value is considered missing if it's None, which typically indicates
        that the configuration key was not found in the configuration file.
        
        Args:
            value: The configuration value to check
            
        Returns:
            bool: True if the value is missing, False otherwise
            
        Examples:
            >>> ConfigurationBlankHandler.is_missing_value(None)
            True
            >>> ConfigurationBlankHandler.is_missing_value("")
            False
            >>> ConfigurationBlankHandler.is_missing_value("value")
            False
        """
        return value is None
    
    @staticmethod
    def should_apply_fallback(value: Any) -> bool:
        """
        Determine if fallback should be applied to a configuration value.
        
        Fallback should only be applied for truly missing values (None),
        not for intentionally blank values. This preserves the user's
        explicit choice to disable a feature by blanking the configuration.
        
        Args:
            value: The configuration value to check
            
        Returns:
            bool: True if fallback should be applied, False otherwise
            
        Examples:
            >>> ConfigurationBlankHandler.should_apply_fallback(None)
            True
            >>> ConfigurationBlankHandler.should_apply_fallback("")
            False
            >>> ConfigurationBlankHandler.should_apply_fallback("   ")
            False
            >>> ConfigurationBlankHandler.should_apply_fallback("*-CORE-*")
            False
        """
        return value is None
    
    @staticmethod
    def process_site_boundary_pattern(raw_value: Optional[str], 
                                    default_pattern: str = "*-CORE-*",
                                    logger: Optional[logging.Logger] = None) -> Optional[str]:
        """
        Process site boundary pattern configuration with proper blank handling.
        
        This method implements the core logic for handling site boundary patterns:
        - Missing values (None) get the default pattern for backward compatibility
        - Blank values (empty/whitespace) return None to disable site boundary detection
        - Valid patterns are returned as-is after trimming whitespace
        
        Args:
            raw_value: The raw configuration value from the INI file
            default_pattern: The default pattern to use for missing values
            logger: Optional logger for recording configuration decisions
            
        Returns:
            Optional[str]: The processed pattern value:
                - None: Site boundary detection disabled (blank pattern)
                - str: Site boundary detection enabled with pattern
                
        Examples:
            >>> ConfigurationBlankHandler.process_site_boundary_pattern(None)
            '*-CORE-*'
            >>> ConfigurationBlankHandler.process_site_boundary_pattern("")
            None
            >>> ConfigurationBlankHandler.process_site_boundary_pattern("   ")
            None
            >>> ConfigurationBlankHandler.process_site_boundary_pattern("*-SITE-*")
            '*-SITE-*'
        """
        if logger is None:
            logger = logging.getLogger(__name__)
        
        if ConfigurationBlankHandler.is_missing_value(raw_value):
            # Missing value - apply default for backward compatibility
            logger.info(f"Site boundary pattern missing from configuration, applying default: {default_pattern}")
            return default_pattern
        elif ConfigurationBlankHandler.is_blank_value(raw_value):
            # Intentionally blank - disable site boundary detection
            logger.info("Site boundary pattern is blank, disabling site boundary detection")
            return None
        else:
            # Valid pattern - use as-is after trimming
            pattern = raw_value.strip()
            logger.info(f"Site boundary pattern loaded: {pattern}")
            return pattern
    
    @staticmethod
    def validate_blank_pattern_as_disabled(pattern: Optional[str]) -> bool:
        """
        Validate that a blank pattern is properly treated as disabled state.
        
        This method confirms that the configuration system correctly interprets
        None values as disabled site boundary detection.
        
        Args:
            pattern: The processed site boundary pattern
            
        Returns:
            bool: True if pattern represents disabled state, False otherwise
            
        Examples:
            >>> ConfigurationBlankHandler.validate_blank_pattern_as_disabled(None)
            True
            >>> ConfigurationBlankHandler.validate_blank_pattern_as_disabled("")
            False
            >>> ConfigurationBlankHandler.validate_blank_pattern_as_disabled("*-CORE-*")
            False
        """
        return pattern is None
    
    @staticmethod
    def get_whitespace_variations() -> list:
        """
        Get a list of various whitespace characters for testing purposes.
        
        This method returns common whitespace characters that should be
        treated as blank values in configuration.
        
        Returns:
            list: List of whitespace character strings
        """
        return [
            "",           # Empty string
            " ",          # Single space
            "  ",         # Multiple spaces
            "\t",         # Tab
            "\n",         # Newline
            "\r",         # Carriage return
            "\r\n",       # Windows line ending
            " \t ",       # Mixed whitespace
            "\t\n\r ",    # Multiple whitespace types
            "   \t\n  ",  # Complex whitespace combination
        ]
    
    @staticmethod
    def handle_unicode_whitespace(value: str) -> str:
        """
        Handle Unicode whitespace characters by normalizing them to ASCII equivalents.
        
        This method addresses edge cases with Unicode whitespace characters that
        might not be properly detected by standard string.strip() operations.
        
        Args:
            value: String value that may contain Unicode whitespace
            
        Returns:
            Normalized string with Unicode whitespace converted to ASCII
        """
        if not isinstance(value, str):
            return value
        
        # Unicode whitespace characters to normalize
        unicode_whitespace_map = {
            '\u00A0': ' ',    # Non-breaking space
            '\u1680': ' ',    # Ogham space mark
            '\u2000': ' ',    # En quad
            '\u2001': ' ',    # Em quad
            '\u2002': ' ',    # En space
            '\u2003': ' ',    # Em space
            '\u2004': ' ',    # Three-per-em space
            '\u2005': ' ',    # Four-per-em space
            '\u2006': ' ',    # Six-per-em space
            '\u2007': ' ',    # Figure space
            '\u2008': ' ',    # Punctuation space
            '\u2009': ' ',    # Thin space
            '\u200A': ' ',    # Hair space
            '\u202F': ' ',    # Narrow no-break space
            '\u205F': ' ',    # Medium mathematical space
            '\u3000': ' ',    # Ideographic space
            '\u180E': ' ',    # Mongolian vowel separator
            '\u200B': '',     # Zero width space
            '\u200C': '',     # Zero width non-joiner
            '\u200D': '',     # Zero width joiner
            '\uFEFF': '',     # Zero width no-break space (BOM)
        }
        
        # Replace Unicode whitespace with ASCII equivalents
        normalized_value = value
        for unicode_char, ascii_replacement in unicode_whitespace_map.items():
            normalized_value = normalized_value.replace(unicode_char, ascii_replacement)
        
        return normalized_value
    
    @staticmethod
    def handle_mixed_content(value: str) -> bool:
        """
        Handle mixed content (whitespace + non-whitespace) edge cases.
        
        This method determines if a string with mixed content should be
        considered blank or valid based on the ratio of whitespace to content.
        
        Args:
            value: String value to analyze
            
        Returns:
            True if should be treated as blank, False if valid content
        """
        if not isinstance(value, str) or not value:
            return True
        
        # Normalize Unicode whitespace first
        normalized_value = ConfigurationBlankHandler.handle_unicode_whitespace(value)
        
        # Count whitespace vs non-whitespace characters
        total_chars = len(normalized_value)
        whitespace_chars = len(normalized_value) - len(normalized_value.strip())
        
        if total_chars == 0:
            return True
        
        # If string is only whitespace after normalization
        if normalized_value.strip() == "":
            return True
        
        # If more than 90% whitespace, consider it effectively blank
        whitespace_ratio = whitespace_chars / total_chars
        if whitespace_ratio > 0.9:
            return True
        
        return False
    
    @staticmethod
    def process_site_boundary_pattern_with_unicode(raw_value: Optional[str], 
                                                  default_pattern: str = "*-CORE-*",
                                                  logger: Optional[logging.Logger] = None) -> Optional[str]:
        """
        Enhanced site boundary pattern processing with Unicode whitespace handling.
        
        This method extends the standard processing to handle Unicode whitespace
        characters and mixed content edge cases that could cause issues on
        different systems or with copy-paste operations.
        
        Args:
            raw_value: The raw configuration value from the INI file
            default_pattern: The default pattern to use for missing values
            logger: Optional logger for recording configuration decisions
            
        Returns:
            Optional[str]: The processed pattern value:
                - None: Site boundary detection disabled (blank pattern)
                - str: Site boundary detection enabled with pattern
        """
        if logger is None:
            logger = logging.getLogger(__name__)
        
        if ConfigurationBlankHandler.is_missing_value(raw_value):
            # Missing value - apply default for backward compatibility
            logger.info(f"Site boundary pattern missing from configuration, applying default: {default_pattern}")
            return default_pattern
        
        # Handle Unicode whitespace normalization
        normalized_value = ConfigurationBlankHandler.handle_unicode_whitespace(raw_value)
        logger.debug(f"Unicode normalization: '{raw_value}' -> '{normalized_value}'")
        
        # Check for mixed content edge cases
        if ConfigurationBlankHandler.handle_mixed_content(normalized_value):
            # Effectively blank after Unicode normalization and mixed content analysis
            logger.info("Site boundary pattern contains only whitespace/mixed content, disabling site boundary detection")
            return None
        elif ConfigurationBlankHandler.is_blank_value(normalized_value):
            # Standard blank detection
            logger.info("Site boundary pattern is blank, disabling site boundary detection")
            return None
        else:
            # Valid pattern - use normalized and trimmed value
            pattern = normalized_value.strip()
            logger.info(f"Site boundary pattern loaded (Unicode normalized): {pattern}")
            return pattern
    
    @staticmethod
    def validate_character_encoding(value: str) -> Tuple[bool, str]:
        """
        Validate character encoding and provide encoding information.
        
        This method helps identify potential encoding issues that could
        cause problems with configuration parsing.
        
        Args:
            value: String value to validate
            
        Returns:
            Tuple of (is_valid, encoding_info)
        """
        if not isinstance(value, str):
            return True, "Not a string"
        
        try:
            # Try to encode as UTF-8 and decode back
            encoded = value.encode('utf-8')
            decoded = encoded.decode('utf-8')
            
            if decoded == value:
                # Check for problematic characters
                problematic_chars = []
                for char in value:
                    if ord(char) > 127:  # Non-ASCII character
                        problematic_chars.append(f"U+{ord(char):04X}")
                
                if problematic_chars:
                    return True, f"Contains Unicode characters: {', '.join(problematic_chars[:5])}"
                else:
                    return True, "ASCII only"
            else:
                return False, "UTF-8 encoding/decoding mismatch"
                
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            return False, f"Encoding error: {str(e)}"