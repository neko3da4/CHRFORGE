# -*- coding: utf-8 -*-
"""
Legacy compatibility module for CHRFORGE configuration.
This module provides backward compatibility with the original config.py interface
while using the new modular configuration system.

For new code, prefer importing from the config package directly:
    from CHRFORGE.config import ClientConfiguration, DeviceType, EndpointRegistry
"""

# Import required symbols from the new config package for backward compatibility
from CHRFORGE.config import (
    DeviceType,
    DeviceDetails,
    DeviceConfigurationFactory,
    get_device_details,
    is_v3_supported,
    APIEndpoint,
    EndpointType,
    EndpointRegistry,
    DomainConfiguration,
    ClientConfiguration,
    RegexPatterns,
    DEFAULT_LANGUAGE,
    DEFAULT_SERVICE_REGION,
)
from CHRFORGE.config.client_config import Config

# Re-export the main Config class for backward compatibility
__all__ = [
    "Config",
    "DeviceType",
    "DeviceDetails",
    "DeviceConfigurationFactory",
    "get_device_details",
    "is_v3_supported",
    "APIEndpoint",
    "EndpointType",
    "EndpointRegistry",
    "DomainConfiguration",
    "ClientConfiguration",
    "RegexPatterns",
    "DEFAULT_LANGUAGE",
    "DEFAULT_SERVICE_REGION",
]

# Legacy constants for backward compatibility
LINE_LANGUAGE = DEFAULT_LANGUAGE
LINE_SERVICE_REGION = DEFAULT_SERVICE_REGION


# Legacy function aliases
def getDeviceDetails(device, version=None):
    """Legacy function alias for get_device_details."""
    return get_device_details(device, version)


def isV3Support(device):
    """Legacy function alias for is_v3_supported."""
    return is_v3_supported(device)
