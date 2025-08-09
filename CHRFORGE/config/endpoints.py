# -*- coding: utf-8 -*-
"""
API endpoints configuration module for CHRFORGE client.
Provides centralized endpoint management with environment variable support.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin


class EndpointType(Enum):
    """Enumeration of endpoint categories."""

    ENCRYPTION = "encryption"
    AUTHENTICATION = "authentication"
    MESSAGING = "messaging"
    CHANNEL = "channel"
    COMMERCE = "commerce"
    SOCIAL = "social"
    UTILITY = "utility"
    EXTERNAL = "external"
    NOTIFICATION = "notification"
    CALL = "call"
    SQUARE = "square"
    E2EE = "e2ee"


@dataclass(frozen=True)
class APIEndpoint:
    """Immutable endpoint configuration."""

    path: str
    endpoint_type: EndpointType
    description: str = ""
    deprecated: bool = False
    version: Optional[str] = None

    def get_full_url(self, base_domain: str) -> str:
        """Get full URL by combining base domain and endpoint path."""
        return urljoin(base_domain.rstrip("/") + "/", self.path.lstrip("/"))


@dataclass
class DomainConfiguration:
    """Configuration for LINE API domains with environment variable support."""

    line_host: str = field(
        default_factory=lambda: os.getenv("LINE_HOST_DOMAIN", "http://localhost:8111")
    )
    line_obs: str = field(
        default_factory=lambda: os.getenv("LINE_OBS_DOMAIN", "http://localhost:8112")
    )
    line_api: str = field(
        default_factory=lambda: os.getenv("LINE_API_DOMAIN", "http://localhost:8113")
    )
    line_access: str = field(
        default_factory=lambda: os.getenv("LINE_ACCESS_DOMAIN", "http://localhost:8114")
    )
    line_biz_timeline: str = field(
        default_factory=lambda: os.getenv(
            "LINE_BIZ_TIMELINE_DOMAIN", "http://localhost:8121"
        )
    )

    def reload_from_environment(self) -> None:
        """Reload domain configuration from environment variables."""
        self.line_host = os.getenv("LINE_HOST_DOMAIN", self.line_host)
        self.line_obs = os.getenv("LINE_OBS_DOMAIN", self.line_obs)
        self.line_api = os.getenv("LINE_API_DOMAIN", self.line_api)
        self.line_access = os.getenv("LINE_ACCESS_DOMAIN", self.line_access)
        self.line_biz_timeline = os.getenv(
            "LINE_BIZ_TIMELINE_DOMAIN", self.line_biz_timeline
        )

    def get_domain_for_endpoint(self, endpoint_path: str) -> str:
        """Get appropriate domain for an endpoint path."""
        # Map specific endpoints to domains
        if endpoint_path.startswith("/BEACON"):
            return self.line_obs
        elif endpoint_path.startswith("/CH") or endpoint_path.startswith("/CHANNEL"):
            return self.line_api
        elif endpoint_path.startswith("/SQ") or endpoint_path.startswith("/SQUARE"):
            return self.line_api
        else:
            return self.line_host


class EndpointRegistry:
    """Registry for managing all LINE API endpoints."""

    # Exception types mapping from TypeScript RequestClient.EXCEPTION_TYPES
    EXCEPTION_TYPES: Dict[str, str] = {
        "/S3": "TalkException",
        "/S4": "TalkException",
        "/SYNC4": "TalkException",
        "/SYNC3": "TalkException",
        "/CH3": "ChannelException",
        "/CH4": "ChannelException",
        "/SQ1": "SquareException",
        "/LIFF1": "LiffException",
        "/api/v3p/rs": "TalkException",
        "/api/v3/TalkService.do": "TalkException",
    }

    # Square endpoints from TypeScript
    SQUARE_ENDPOINTS: Set[str] = {"/SQ1", "/SQLV1"}

    def __init__(self):
        self._endpoints: Dict[str, APIEndpoint] = {}
        self._domain_config = DomainConfiguration()
        self._register_default_endpoints()

    def _register_default_endpoints(self) -> None:
        """Register all default LINE API endpoints."""

        # Encryption endpoints
        self.register(
            APIEndpoint("/enc", EndpointType.ENCRYPTION, "Encryption endpoint")
        )

        # Authentication endpoints
        self.register(
            APIEndpoint("/ACS4", EndpointType.AUTHENTICATION, "Age check endpoint")
        )
        self.register(APIEndpoint("/RS3", EndpointType.AUTHENTICATION, "Auth endpoint"))
        self.register(
            APIEndpoint("/RS4", EndpointType.AUTHENTICATION, "Auth endpoint V4")
        )
        self.register(
            APIEndpoint(
                "/ACCT/authfactor/eap/v1",
                EndpointType.AUTHENTICATION,
                "EAP auth endpoint",
            )
        )
        self.register(
            APIEndpoint(
                "/acct/lgn/sq/v1", EndpointType.AUTHENTICATION, "Secondary QR login"
            )
        )
        self.register(
            APIEndpoint(
                "/acct/lgn/secpwless/v1",
                EndpointType.AUTHENTICATION,
                "Secondary passwordless login",
            )
        )
        self.register(
            APIEndpoint(
                "/acct/lp/lgn/secpwless/v1",
                EndpointType.AUTHENTICATION,
                "Secondary passwordless login permit",
            )
        )
        self.register(
            APIEndpoint(
                "/acct/authfactor/second/pincode/v1",
                EndpointType.AUTHENTICATION,
                "Secondary auth factor PIN",
            )
        )
        self.register(
            APIEndpoint(
                "/acct/authfactor/pwless/manage/v1",
                EndpointType.AUTHENTICATION,
                "Passwordless credential management",
            )
        )
        self.register(
            APIEndpoint(
                "/ACCT/authfactor/pwless/v1",
                EndpointType.AUTHENTICATION,
                "Passwordless primary registration",
            )
        )
        self.register(
            APIEndpoint(
                "/LF1",
                EndpointType.AUTHENTICATION,
                "Secondary device login verify PIN with E2EE",
            )
        )
        self.register(
            APIEndpoint(
                "/Q", EndpointType.AUTHENTICATION, "Secondary device login verify PIN"
            )
        )

        # Messaging endpoints
        self.register(
            APIEndpoint("/S3", EndpointType.MESSAGING, "Normal messaging endpoint")
        )
        self.register(
            APIEndpoint("/C5", EndpointType.MESSAGING, "Compact message endpoint")
        )
        self.register(
            APIEndpoint(
                "/CA5", EndpointType.MESSAGING, "Compact plain message endpoint"
            )
        )
        self.register(
            APIEndpoint("/ECA5", EndpointType.E2EE, "Compact E2EE message endpoint")
        )
        self.register(
            APIEndpoint("/CP4", EndpointType.MESSAGING, "Cancel long polling endpoint")
        )
        self.register(
            APIEndpoint("/R2", EndpointType.UTILITY, "Connection info endpoint")
        )

        # Channel endpoints
        self.register(APIEndpoint("/CH3", EndpointType.CHANNEL, "Channel endpoint"))
        self.register(APIEndpoint("/CH4", EndpointType.CHANNEL, "Channel endpoint V4"))
        self.register(APIEndpoint("/PS4", EndpointType.CHANNEL, "Personal endpoint V4"))
        self.register(APIEndpoint("/CAPP1", EndpointType.CHANNEL, "Chat app endpoint"))

        # Commerce endpoints
        self.register(APIEndpoint("/COIN4", EndpointType.COMMERCE, "Coin endpoint"))
        self.register(APIEndpoint("/SHOP3", EndpointType.COMMERCE, "Shop endpoint"))
        self.register(
            APIEndpoint("/SHOPA", EndpointType.COMMERCE, "Shop auth endpoint")
        )
        self.register(
            APIEndpoint("/TSHOP4", EndpointType.COMMERCE, "Unified shop endpoint")
        )
        self.register(APIEndpoint("/WALLET4", EndpointType.COMMERCE, "Wallet endpoint"))

        # Social endpoints
        self.register(APIEndpoint("/SQ1", EndpointType.SQUARE, "Square endpoint"))
        self.register(APIEndpoint("/BP1", EndpointType.SQUARE, "Square bot endpoint"))
        self.register(APIEndpoint("/BUDDY3", EndpointType.SOCIAL, "Buddy endpoint"))
        self.register(
            APIEndpoint(
                "/SNS4", EndpointType.SOCIAL, "SNS adapter endpoint", deprecated=True
            )
        )  # Keeping for backward compatibility
        self.register(APIEndpoint("/SA4", EndpointType.SOCIAL, "SNS adapter endpoint"))
        self.register(
            APIEndpoint("/api/v4p/sa", EndpointType.SOCIAL, "SNS adapter registration")
        )

        # Call endpoints
        self.register(APIEndpoint("/V3", EndpointType.CALL, "Call endpoint"))
        self.register(
            APIEndpoint(
                "/EXT/groupcall/youtube-api",
                EndpointType.EXTERNAL,
                "VoIP group call YouTube",
            )
        )

        # Utility endpoints
        self.register(APIEndpoint("/BEACON4", EndpointType.UTILITY, "Beacon endpoint"))
        self.register(APIEndpoint("/IOT1", EndpointType.UTILITY, "IoT endpoint"))
        self.register(APIEndpoint("/LIFF1", EndpointType.UTILITY, "LIFF endpoint"))
        self.register(
            APIEndpoint("/F4", EndpointType.NOTIFICATION, "Notify sleep endpoint")
        )

        # External/Integration endpoints
        self.register(
            APIEndpoint("/EIS4", EndpointType.EXTERNAL, "External interlock endpoint")
        )

        # E2EE endpoints
        self.register(
            APIEndpoint("/EKBS4", EndpointType.E2EE, "E2EE key backup endpoint")
        )

    def register(self, endpoint: APIEndpoint) -> None:
        """Register a new endpoint."""
        self._endpoints[endpoint.path] = endpoint

    def get_endpoint(self, path: str) -> Optional[APIEndpoint]:
        """Get endpoint by path."""
        return self._endpoints.get(path)

    def get_endpoints_by_type(self, endpoint_type: EndpointType) -> List[APIEndpoint]:
        """Get all endpoints of a specific type."""
        return [
            ep for ep in self._endpoints.values() if ep.endpoint_type == endpoint_type
        ]

    def get_all_endpoints(self) -> List[APIEndpoint]:
        """Get all registered endpoints."""
        return list(self._endpoints.values())

    def get_full_url(self, path: str, custom_domain: Optional[str] = None) -> str:
        """Get full URL for an endpoint path."""
        if custom_domain:
            base_domain = custom_domain
        else:
            base_domain = self._domain_config.get_domain_for_endpoint(path)

        return urljoin(base_domain.rstrip("/") + "/", path.lstrip("/"))

    def get_exception_type(self, path: str) -> Optional[str]:
        """Get exception type for endpoint path."""
        return self.EXCEPTION_TYPES.get(path)

    def is_square_endpoint(self, path: str) -> bool:
        """Check if endpoint is a Square endpoint."""
        return path in self.SQUARE_ENDPOINTS

    def reload_domains(self) -> None:
        """Reload domain configuration from environment variables."""
        self._domain_config.reload_from_environment()

    @property
    def domain_config(self) -> DomainConfiguration:
        """Get domain configuration."""
        return self._domain_config

    # Convenience methods for common endpoint categories
    def get_auth_endpoints(self) -> List[APIEndpoint]:
        """Get authentication endpoints."""
        return self.get_endpoints_by_type(EndpointType.AUTHENTICATION)

    def get_messaging_endpoints(self) -> List[APIEndpoint]:
        """Get messaging endpoints."""
        return self.get_endpoints_by_type(EndpointType.MESSAGING)

    def get_channel_endpoints(self) -> List[APIEndpoint]:
        """Get channel endpoints."""
        return self.get_endpoints_by_type(EndpointType.CHANNEL)

    def get_commerce_endpoints(self) -> List[APIEndpoint]:
        """Get commerce endpoints."""
        return self.get_endpoints_by_type(EndpointType.COMMERCE)

    def get_square_endpoints(self) -> List[APIEndpoint]:
        """Get Square endpoints."""
        return self.get_endpoints_by_type(EndpointType.SQUARE)

    def get_e2ee_endpoints(self) -> List[APIEndpoint]:
        """Get E2EE endpoints."""
        return self.get_endpoints_by_type(EndpointType.E2EE)


# Global endpoint registry instance
_endpoint_registry = EndpointRegistry()


# Convenience functions for easy access
def get_endpoint_registry() -> EndpointRegistry:
    """Get the global endpoint registry instance."""
    return _endpoint_registry


def get_full_url(path: str, custom_domain: Optional[str] = None) -> str:
    """Get full URL for an endpoint path."""
    return _endpoint_registry.get_full_url(path, custom_domain)


def get_exception_type(path: str) -> Optional[str]:
    """Get exception type for endpoint path."""
    return _endpoint_registry.get_exception_type(path)


def is_square_endpoint(path: str) -> bool:
    """Check if endpoint is a Square endpoint."""
    return _endpoint_registry.is_square_endpoint(path)


def reload_domains() -> None:
    """Reload domain configuration from environment variables."""
    _endpoint_registry.reload_domains()
