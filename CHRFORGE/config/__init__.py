# -*- coding: utf-8 -*-
"""
Configuration package for CHRFORGE client.
Provides device configurations, endpoint management, and client settings.
"""

from CHRFORGE.config.devices import (
    DeviceType,
    DeviceDetails,
    DeviceConfigurationFactory,
    get_device_details,
    is_v3_supported,
)
from CHRFORGE.config.endpoints import (
    APIEndpoint,
    EndpointType,
    EndpointRegistry,
    DomainConfiguration,
)
from CHRFORGE.config.client_config import (
    ClientConfiguration,
    RegexPatterns,
    DEFAULT_LANGUAGE,
    DEFAULT_SERVICE_REGION,
)

__all__ = [
    # Device configuration
    "DeviceType",
    "DeviceDetails",
    "DeviceConfigurationFactory",
    "get_device_details",
    "is_v3_supported",
    # Endpoint configuration
    "APIEndpoint",
    "EndpointType",
    "EndpointRegistry",
    "DomainConfiguration",
    # Client configuration
    "ClientConfiguration",
    "RegexPatterns",
    "DEFAULT_LANGUAGE",
    "DEFAULT_SERVICE_REGION",
]
