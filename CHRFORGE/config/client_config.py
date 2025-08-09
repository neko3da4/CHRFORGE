# -*- coding: utf-8 -*-
"""
Client configuration module for CHRFORGE client.
Provides core client settings, regex patterns, and configuration management.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .devices import DeviceType, DeviceDetails, DeviceConfigurationFactory
from .endpoints import EndpointRegistry


# Constants matching original config
DEFAULT_LANGUAGE = "zh-Hant_TW"
DEFAULT_SERVICE_REGION = "TW"
DEFAULT_IP_ADDR = "8.8.8.8"


@dataclass(frozen=True)
class RegexPatterns:
    """Collection of regex patterns used throughout the client."""

    # Email validation pattern
    email: re.Pattern[str] = field(
        default_factory=lambda: re.compile(r"[^@]+@[^@]+\.[^@]+")
    )

    # Consent form patterns
    consent_channel_id: re.Pattern[str] = field(
        default_factory=lambda: re.compile(
            r'<input type="hidden" name="channelId" value="([^"]+)"'
        )
    )
    consent_csrf_token: re.Pattern[str] = field(
        default_factory=lambda: re.compile(
            r'<input type="hidden" name="__csrf" id="__csrf" value="([^"]+)"'
        )
    )

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        return bool(self.email.match(email))

    def extract_consent_channel_id(self, html: str) -> Optional[str]:
        """Extract channel ID from consent form HTML."""
        match = self.consent_channel_id.search(html)
        return match.group(1) if match else None

    def extract_consent_csrf_token(self, html: str) -> Optional[str]:
        """Extract CSRF token from consent form HTML."""
        match = self.consent_csrf_token.search(html)
        return match.group(1) if match else None


@dataclass
class ClientConfiguration:
    """
    Main configuration class for CHRFORGE client.
    Combines device settings, endpoints, and client-specific configurations.
    """

    # Core settings
    language: str = DEFAULT_LANGUAGE
    service_region: str = DEFAULT_SERVICE_REGION
    ip_address: str = DEFAULT_IP_ADDR

    # Device configuration
    device_details: Optional[DeviceDetails] = None

    # Registry instances
    endpoint_registry: EndpointRegistry = field(default_factory=EndpointRegistry)
    regex_patterns: RegexPatterns = field(default_factory=RegexPatterns)

    # Custom configurations
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default device if none provided."""
        if self.device_details is None:
            # Default to CHROMEOS like original config
            config = DeviceConfigurationFactory.create_config(DeviceType.CHROMEOS)
            object.__setattr__(self, "device_details", config.get_device_details())

    @classmethod
    def create_with_device(
        cls,
        device_type: str,
        app_version: Optional[str] = None,
        os_name: Optional[str] = None,
        os_version: Optional[str] = None,
        os_model: Optional[str] = None,
        support_v3_token: Optional[bool] = None,
        support_sync: Optional[bool] = None,
        **kwargs,
    ) -> ClientConfiguration:
        """
        Create configuration with specific device settings.
        Matches the interface of the original Config.__init__ method.
        """
        try:
            device_enum = DeviceType(device_type)
            config_strategy = DeviceConfigurationFactory.create_config(device_enum)
            device_details = config_strategy.get_device_details(app_version)
        except ValueError:
            # Handle custom device types
            if not all([app_version, os_name, os_version]):
                raise ValueError(
                    f"You need to specify `app_version`, `os_name` and `os_version` "
                    f"to use this device type: {device_type}"
                )

            device_enum = (
                DeviceType(device_type)
                if device_type in [dt.value for dt in DeviceType]
                else DeviceType.CHROMEOS
            )
            custom_config = DeviceConfigurationFactory.create_custom_config(
                device_enum, app_version, os_name, os_version, os_model
            )
            device_details = custom_config.get_device_details()

        return cls(device_details=device_details, **kwargs)

    @property
    def app_name(self) -> str:
        """Get formatted app name string."""
        return self.device_details.app_name if self.device_details else ""

    @property
    def user_agent(self) -> str:
        """Get user agent string."""
        return self.device_details.user_agent if self.device_details else ""

    @property
    def system_type(self) -> str:
        """Get system type string matching TypeScript RequestClient format."""
        if not self.device_details:
            return ""

        return (
            f"{self.device_details.device.value}\t{self.device_details.app_version}\t"
            f"{self.device_details.system_name}\t{self.device_details.system_version}"
        )

    def supports_v3_token(self) -> bool:
        """Check if current device supports V3 tokens."""
        if not self.device_details:
            return False
        return DeviceConfigurationFactory.is_v3_token_supported(
            self.device_details.device
        )

    def supports_sync(self) -> bool:
        """Check if current device supports sync."""
        if not self.device_details:
            return False
        return DeviceConfigurationFactory.is_sync_supported(self.device_details.device)

    def is_secondary_device(self) -> bool:
        """Check if device is configured as secondary."""
        return self.device_details.is_secondary if self.device_details else False

    def get_endpoint_url(self, path: str, custom_domain: Optional[str] = None) -> str:
        """Get full URL for an endpoint path."""
        return self.endpoint_registry.get_full_url(path, custom_domain)

    def get_exception_type(self, path: str) -> Optional[str]:
        """Get exception type for endpoint path."""
        return self.endpoint_registry.get_exception_type(path)

    def is_square_endpoint(self, path: str) -> bool:
        """Check if endpoint is a Square endpoint."""
        return self.endpoint_registry.is_square_endpoint(path)

    def reload_domains(self) -> None:
        """Reload domain configuration from environment variables."""
        self.endpoint_registry.reload_domains()

    def update_device_config(
        self, device_type: str, version: Optional[str] = None
    ) -> None:
        """Update device configuration."""
        config_strategy = DeviceConfigurationFactory.create_config(device_type)
        object.__setattr__(
            self, "device_details", config_strategy.get_device_details(version)
        )

    def get_request_headers(
        self, method: str = "POST", additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Get HTTP headers for requests matching TypeScript RequestClient.getHeader.
        """
        if not self.device_details:
            raise ValueError("Device details not configured")

        # Get the appropriate domain (assuming we use line_host as default)
        endpoint_host = self.endpoint_registry.domain_config.line_host.replace(
            "http://", ""
        ).replace("https://", "")

        headers = {
            "Host": endpoint_host,
            "accept": "application/x-thrift",
            "user-agent": self.user_agent,
            "x-line-application": self.system_type,
            "content-type": "application/x-thrift",
            "x-lal": self.language,
            "x-lpv": "1",
            "x-lhm": method,
            "accept-encoding": "gzip",
        }

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def validate_email(self, email: str) -> bool:
        """Validate email format using regex patterns."""
        return self.regex_patterns.validate_email(email)

    def extract_consent_data(self, html: str) -> Dict[str, Optional[str]]:
        """Extract consent form data from HTML."""
        return {
            "channel_id": self.regex_patterns.extract_consent_channel_id(html),
            "csrf_token": self.regex_patterns.extract_consent_csrf_token(html),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {
            "language": self.language,
            "service_region": self.service_region,
            "ip_address": self.ip_address,
            "custom_settings": self.custom_settings,
        }

        if self.device_details:
            result["device_details"] = {
                "device": self.device_details.device.value,
                "app_version": self.device_details.app_version,
                "system_name": self.device_details.system_name,
                "system_version": self.device_details.system_version,
                "system_model": self.device_details.system_model,
                "user_domain": self.device_details.user_domain,
                "is_secondary": self.device_details.is_secondary,
            }

        return result

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> ClientConfiguration:
        """Create configuration from dictionary."""
        device_data = config_dict.pop("device_details", None)
        device_details = None

        if device_data:
            device_details = DeviceDetails(
                device=DeviceType(device_data["device"]),
                app_version=device_data["app_version"],
                system_name=device_data["system_name"],
                system_version=device_data.get("system_version", "12.1.4"),
                system_model=device_data.get("system_model", "System Product Name"),
                user_domain=device_data.get("user_domain", "KORONE-MY-WAIFU"),
                is_secondary=device_data.get("is_secondary", False),
            )

        return cls(device_details=device_details, **config_dict)

    def __repr__(self) -> str:
        """String representation of configuration."""
        device_info = (
            f"Device: {self.device_details.device.value}"
            if self.device_details
            else "No device"
        )
        return f"ClientConfiguration({device_info}, Language: {self.language}, Region: {self.service_region})"


# Backward compatibility class matching original Config interface
class Config(ClientConfiguration):
    """
    Backward compatibility wrapper for the original Config class.
    Provides the same interface as the original implementation.
    """

    def __init__(
        self,
        type: str,
        app_version: Optional[str] = None,
        os_name: Optional[str] = None,
        os_version: Optional[str] = None,
        os_model: Optional[str] = None,
        *,
        support_v3_token: Optional[bool] = None,
        support_sync: Optional[bool] = None,
    ):
        """
        Initialize Config with original interface.
        Maps to new ClientConfiguration.create_with_device method.
        """
        config = ClientConfiguration.create_with_device(
            device_type=type,
            app_version=app_version,
            os_name=os_name,
            os_version=os_version,
            os_model=os_model,
            support_v3_token=support_v3_token,
            support_sync=support_sync,
        )

        # Copy all attributes from the created configuration
        super().__init__(
            language=config.language,
            service_region=config.service_region,
            ip_address=config.ip_address,
            device_details=config.device_details,
            endpoint_registry=config.endpoint_registry,
            regex_patterns=config.regex_patterns,
            custom_settings=config.custom_settings,
        )

        # Set legacy attributes for backward compatibility
        self._init_legacy_attributes()

    def _init_legacy_attributes(self) -> None:
        """Initialize legacy attributes for backward compatibility."""
        if self.device_details:
            self.APP_TYPE = self.device_details.device.value
            self.APP_VER = self.device_details.app_version
            self.SYSTEM_NAME = self.device_details.system_name
            self.SYSTEM_VER = self.device_details.system_version
            self.SYSTEM_MODEL = self.device_details.system_model
            self.USERDOMAIN = self.device_details.user_domain
            self.isSecondary = self.device_details.is_secondary
            self.APP_NAME = self.device_details.app_name
            self.USER_AGENT = self.device_details.user_agent

        # Legacy constants
        self.LINE_LANGUAGE = self.language
        self.LINE_SERVICE_REGION = self.service_region
        self.IP_ADDR = self.ip_address
        self.EMAIL_REGEX = self.regex_patterns.email
        self.CONSENT_CHANNEL_ID_REGEX = self.regex_patterns.consent_channel_id
        self.CONSENT_CSRF_TOKEN_REGEX = self.regex_patterns.consent_csrf_token

        # Legacy endpoint constants
        self._init_legacy_endpoints()

        # Legacy support lists
        self.TOKEN_V3_SUPPORT = [
            dt.value
            for dt in DeviceType
            if DeviceConfigurationFactory.is_v3_token_supported(dt)
        ]
        self.SYNC_SUPPORT = [
            dt.value
            for dt in DeviceType
            if DeviceConfigurationFactory.is_sync_supported(dt)
        ]

    def _init_legacy_endpoints(self) -> None:
        """Initialize legacy endpoint constants."""
        domain_config = self.endpoint_registry.domain_config

        # Domain constants
        self.LINE_HOST_DOMAIN = domain_config.line_host
        self.LINE_OBS_DOMAIN = domain_config.line_obs
        self.LINE_API_DOMAIN = domain_config.line_api
        self.LINE_ACCESS_DOMAIN = domain_config.line_access
        self.LINE_BIZ_TIMELINE_DOMAIN = domain_config.line_biz_timeline

        # Endpoint path constants
        self.LINE_ENCRYPTION_ENDPOINT = "/enc"
        self.LINE_AGE_CHECK_ENDPOINT = "/ACS4"
        self.LINE_AUTH_ENDPOINT = "/RS3"
        self.LINE_AUTH_ENDPOINT_V4 = "/RS4"
        self.LINE_AUTH_EAP_ENDPOINT = "/ACCT/authfactor/eap/v1"
        self.LINE_BEACON_ENDPOINT = "/BEACON4"
        self.LINE_BUDDY_ENDPOINT = "/BUDDY3"
        self.LINE_CALL_ENDPOINT = "/V3"
        self.LINE_CANCEL_LONGPOLLING_ENDPOINT = "/CP4"
        self.LINE_CHANNEL_ENDPOINT = "/CH3"
        self.LINE_CHANNEL_ENDPOINT_V4 = "/CH4"
        self.LINE_PERSONAL_ENDPOINT_V4 = "/PS4"
        self.LINE_CHAT_APP_ENDPOINT = "/CAPP1"
        self.LINE_COIN_ENDPOINT = "/COIN4"
        self.LINE_COMPACT_E2EE_MESSAGE_ENDPOINT = "/ECA5"
        self.LINE_COMPACT_MESSAGE_ENDPOINT = "/C5"
        self.LINE_COMPACT_PLAIN_MESSAGE_ENDPOINT = "/CA5"
        self.LINE_CONN_INFO_ENDPOINT = "/R2"
        self.LINE_EXTERNAL_INTERLOCK_ENDPOINT = "/EIS4"
        self.LINE_IOT_ENDPOINT = "/IOT1"
        self.LINE_LIFF_ENDPOINT = "/LIFF1"
        self.LINE_NORMAL_ENDPOINT = "/S3"
        self.LINE_SECONDARY_QR_LOGIN_ENDPOINT = "/acct/lgn/sq/v1"
        self.LINE_SHOP_ENDPOINT = "/SHOP3"
        self.LINE_SHOP_AUTH_ENDPOINT = "/SHOPA"
        self.LINE_SNS_ADAPTER_ENDPOINT = "/SA4"
        self.LINE_SNS_ADAPTER_REGISTRATION_ENDPOINT = "/api/v4p/sa"
        self.LINE_SQUARE_ENDPOINT = "/SQ1"
        self.LINE_SQUARE_BOT_ENDPOINT = "/BP1"
        self.LINE_UNIFIED_SHOP_ENDPOINT = "/TSHOP4"
        self.LINE_WALLET_ENDPOINT = "/WALLET4"
        self.LINE_SECONDARY_PWLESS_LOGIN_ENDPOINT = "/acct/lgn/secpwless/v1"
        self.LINE_SECONDARY_PWLESS_LOGIN_PERMIT_ENDPOINT = "/acct/lp/lgn/secpwless/v1"
        self.LINE_SECONDARY_AUTH_FACTOR_PIN_CODE_ENDPOINT = (
            "/acct/authfactor/second/pincode/v1"
        )
        self.LINE_PWLESS_CREDENTIAL_MANAGEMENT_ENDPOINT = (
            "/acct/authfactor/pwless/manage/v1"
        )
        self.LINE_PWLESS_PRIMARY_REGISTRATION_ENDPOINT = "/ACCT/authfactor/pwless/v1"
        self.LINE_VOIP_GROUP_CALL_YOUTUBE_ENDPOINT = "/EXT/groupcall/youtube-api"
        self.LINE_E2EE_KEY_BACKUP_ENDPOINT = "/EKBS4"
        self.SECONDARY_DEVICE_LOGIN_VERIFY_PIN_WITH_E2EE = "/LF1"
        self.SECONDARY_DEVICE_LOGIN_VERIFY_PIN = "/Q"
        self.LINE_NOTIFY_SLEEP_ENDPOINT = "/F4"

    @property
    def LineUserAgent(self) -> str:
        """Legacy property for user agent."""
        return self.user_agent

    def initAppConfig(
        self,
        app_type: Optional[str],
        app_version: Optional[str],
        os_name: Optional[str],
        os_version: Optional[str],
        os_model: Optional[str],
    ) -> None:
        """Legacy method for updating app config."""
        if app_type:
            try:
                self.update_device_config(app_type, app_version)
            except ValueError:
                # Handle custom device configuration
                if app_version and os_name and os_version:
                    custom_config = DeviceConfigurationFactory.create_custom_config(
                        DeviceType.CHROMEOS, app_version, os_name, os_version, os_model
                    )
                    object.__setattr__(
                        self, "device_details", custom_config.get_device_details()
                    )

        self._init_legacy_attributes()

    def reloadDomains(self) -> None:
        """Legacy method for reloading domains."""
        self.reload_domains()
        self._init_legacy_endpoints()
