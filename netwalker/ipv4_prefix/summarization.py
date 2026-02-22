"""
Summarization Analyzer Component for IPv4 Prefix Inventory Module

This module analyzes route summarization relationships, identifying summary routes
and their component routes to track hierarchical prefix aggregation.

Author: Mark Oldham
"""

import logging
import ipaddress
from typing import List

from netwalker.ipv4_prefix.data_models import NormalizedPrefix, SummarizationRelationship


class SummarizationAnalyzer:
    """Analyzes route summarization relationships."""
    
    def __init__(self):
        """Initialize summarization analyzer."""
        self.logger = logging.getLogger(__name__)
    
    def analyze_summarization(self, prefixes: List[NormalizedPrefix]) -> List[SummarizationRelationship]:
        """
        Identify summary routes and their component routes.
        
        Algorithm:
        1. Sort prefixes by prefix length (shortest first)
        2. For each prefix, find all more-specific prefixes that fall within its range
        3. Record relationships where a device advertises both summary and components
        
        Args:
            prefixes: List of NormalizedPrefix objects
            
        Returns:
            List of SummarizationRelationship objects
            
        Requirements:
            - 15.3: Identify summary/component relationships
            - 15.5: Record device_id that performed summarization
            - 15.6: Support recursive queries for multi-level hierarchies
            - 15.7: Record both relationships when prefix is both component and summary
        """
        relationships = []
        
        if not prefixes:
            return relationships
        
        # Group prefixes by device and VRF for efficient lookup
        device_vrf_prefixes = {}
        for prefix in prefixes:
            key = (prefix.device, prefix.vrf)
            if key not in device_vrf_prefixes:
                device_vrf_prefixes[key] = []
            device_vrf_prefixes[key].append(prefix)
        
        # Analyze each device/VRF combination independently
        for (device, vrf), prefix_list in device_vrf_prefixes.items():
            # Sort by prefix length (shortest first = most general)
            sorted_prefixes = sorted(prefix_list, key=lambda p: self._get_prefix_length(p.prefix))
            
            # For each prefix, find components
            for i, summary_prefix in enumerate(sorted_prefixes):
                # Check all more-specific prefixes (those that come after in sorted list)
                for component_prefix in sorted_prefixes[i+1:]:
                    # Check if component falls within summary range
                    if self.is_component_of(component_prefix.prefix, summary_prefix.prefix):
                        # Create relationship
                        relationship = SummarizationRelationship(
                            summary_prefix=summary_prefix.prefix,
                            component_prefix=component_prefix.prefix,
                            device=device,
                            vrf=vrf
                        )
                        relationships.append(relationship)
        
        self.logger.info(f"Identified {len(relationships)} summarization relationships")
        return relationships
    
    def is_component_of(self, component: str, summary: str) -> bool:
        """
        Check if component prefix falls within summary prefix range.
        
        Example:
        - 192.168.1.0/24 is component of 192.168.0.0/16
        - 10.1.1.0/24 is component of 10.0.0.0/8
        
        Args:
            component: Component prefix in CIDR notation
            summary: Summary prefix in CIDR notation
            
        Returns:
            True if component falls within summary range
            
        Requirements:
            - 15.3: Identify if component prefix falls within summary range
        """
        try:
            # Parse both prefixes as IPv4Network objects
            component_net = ipaddress.IPv4Network(component, strict=False)
            summary_net = ipaddress.IPv4Network(summary, strict=False)
            
            # Check if component is a subnet of summary
            # A prefix is a component if:
            # 1. It's more specific (longer prefix length)
            # 2. It falls within the summary's address range
            if component_net.prefixlen <= summary_net.prefixlen:
                # Component must be more specific than summary
                return False
            
            # Check if component's network address falls within summary's range
            return component_net.subnet_of(summary_net)
            
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
            self.logger.warning(f"Invalid prefix format in summarization check: {component}, {summary} - {str(e)}")
            return False
    
    def find_components(self, summary: str, all_prefixes: List[NormalizedPrefix]) -> List[NormalizedPrefix]:
        """
        Find all component prefixes for a given summary.
        
        Args:
            summary: Summary prefix in CIDR notation
            all_prefixes: List of all NormalizedPrefix objects to search
            
        Returns:
            List of NormalizedPrefix objects that are components of the summary
            
        Requirements:
            - 15.6: Support finding all components for a summary
        """
        components = []
        
        for prefix in all_prefixes:
            if self.is_component_of(prefix.prefix, summary):
                components.append(prefix)
        
        return components
    
    def _get_prefix_length(self, prefix: str) -> int:
        """
        Get the prefix length from a CIDR notation string.
        
        Args:
            prefix: Prefix in CIDR notation (e.g., "192.168.1.0/24")
            
        Returns:
            Prefix length as integer (e.g., 24)
        """
        try:
            network = ipaddress.IPv4Network(prefix, strict=False)
            return network.prefixlen
        except (ValueError, ipaddress.AddressValueError, ipaddress.NetmaskValueError):
            # If parsing fails, return a large number to sort it last
            return 999
