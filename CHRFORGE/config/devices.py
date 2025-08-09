# -*- coding: utf-8 -*-
"""
Device configuration module for CHRFORGE client.
Provides device-specific settings and configurations in a clean, object-oriented manner.
Includes compatibility and version alignment with TypeScript version.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List, Union


class DeviceType(Enum):
    """Enumeration of supported device types."""

    DESKTOPWIN = "DESKTOPWIN"
    DESKTOPMAC = "DESKTOPMAC"
    CHROMEOS = "CHROMEOS"
    ANDROID = "ANDROID"
    ANDROIDSECONDARY = "ANDROIDSECONDARY"
    IOS = "IOS"
    IOSIPAD = "IOSIPAD"
    WATCHOS = "WATCHOS"
    WEAROS = "WEAROS"
    VISIONOS = "VISIONOS"
    # Special types
    OPENCHAT_PLUS = "OPENCHAT_PLUS"
    CHANNELGW = "CHANNELGW"
    CHANNELCP = "CHANNELCP"
    CLOVAFRIENDS = "CLOVAFRIENDS"
    BOT = "BOT"
    WAP = "WAP"
    WEB = "WEB"
    BIZWEB = "BIZWEB"
    DUMMYPRIMARY = "DUMMYPRIMARY"
    SQUARE = "SQUARE"
    FIREFOXOS = "FIREFOXOS"
    TIZEN = "TIZEN"
    VIRTUAL = "VIRTUAL"
    CHRONO = "CHRONO"
    WINMETRO = "WINMETRO"
    S40 = "S40"
    WINPHONE = "WINPHONE"
    BLACKBERRY = "BLACKBERRY"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class DeviceDetails:
    """Immutable data class representing device configuration details."""

    device: DeviceType
    app_version: str
    system_name: str
    system_version: str = "12.1.4"
    system_model: str = "System Product Name"
    user_domain: str = "KORONE-MY-WAIFU"
    is_secondary: bool = False

    @property
    def app_name(self) -> str:
        """Generate app name string from device details matching TypeScript format."""
        name = f"{self.device.value}\t{self.app_version}\t{self.system_name}\t{self.system_version}"
        return f"{name};SECONDARY" if self.is_secondary else name

    @property
    def user_agent(self) -> str:
        """Generate user agent string based on device type matching TypeScript logic."""
        if self.device == DeviceType.CHROMEOS:
            return (
                "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            )

        if self.device in (DeviceType.DESKTOPWIN, DeviceType.DESKTOPMAC):
            desktop_name = "WINDOWS" if self.device == DeviceType.DESKTOPWIN else "MAC"
            return f"DESKTOP:{desktop_name}:{self.system_version}({self.app_version})"

        return f"Line/{self.app_version} {self.system_model} {self.system_version}"


class DeviceConfigurationStrategy(ABC):
    """Abstract base class for device configuration strategies."""

    @abstractmethod
    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        """Get device details for this configuration strategy."""
        pass

    @property
    @abstractmethod
    def device_type(self) -> DeviceType:
        """Get the device type for this strategy."""
        pass


class DesktopWindowsConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Desktop Windows devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.DESKTOPWIN,
            app_version=version or "9.2.0.3403",
            system_name="WINDOWS",
            system_version="10.0.0-NT-x64",
            system_model="KORONE-MY-WAIFU",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.DESKTOPWIN


class DesktopMacConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Desktop Mac devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.DESKTOPMAC,
            app_version=version or "9.2.0.3402",
            system_name="MAC",
            system_version="12.1.4",
            system_model="KORONE-MY-WAIFU",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.DESKTOPMAC


class ChromeOSConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Chrome OS devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.CHROMEOS,
            app_version=version or "3.0.3",
            system_name="Chrome_OS",
            system_version="1",
            system_model="Chrome",
            user_domain="CHROMEOS",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.CHROMEOS


class AndroidConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Android devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.ANDROID,
            app_version=version or "13.4.1",
            system_name="Android OS",
            system_version="12.1.4",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.ANDROID


class AndroidSecondaryConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Android secondary devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.ANDROIDSECONDARY,
            app_version=version or "13.4.1",
            system_name="Android OS",
            system_version="12.1.4",
            is_secondary=True,
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.ANDROIDSECONDARY


class iOSConfig(DeviceConfigurationStrategy):
    """Configuration strategy for iOS devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.IOS,
            app_version=version or "13.3.0",
            system_name="iOS",
            system_version="12.1.4",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.IOS


class iPadConfig(DeviceConfigurationStrategy):
    """Configuration strategy for iPad devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        # system_name is "iOS" to match TS interface
        return DeviceDetails(
            device=DeviceType.IOSIPAD,
            app_version=version or "13.3.0",
            system_name="iOS",
            system_version="12.1.4",
            system_model="iPad5,1",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.IOSIPAD


class WatchOSConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Apple Watch devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.WATCHOS,
            app_version=version or "13.3.0",
            system_name="Watch OS",
            system_version="12.1.4",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.WATCHOS


class WearOSConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Wear OS devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.WEAROS,
            app_version=version or "13.4.1",
            system_name="Wear OS",
            system_version="12.1.4",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.WEAROS


class VisionOSConfig(DeviceConfigurationStrategy):
    """Configuration strategy for Apple Vision Pro devices."""

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=DeviceType.VISIONOS,
            app_version=version or "1.0.0",
            system_name="visionOS",
            system_version="12.1.4",
            system_model="RealityDevice14,1",
        )

    @property
    def device_type(self) -> DeviceType:
        return DeviceType.VISIONOS


class CustomDeviceConfig(DeviceConfigurationStrategy):
    """Configuration strategy for custom device configurations."""

    def __init__(
        self,
        device_type: DeviceType,
        app_version: str,
        system_name: str,
        system_version: str,
        system_model: Optional[str] = None,
    ):
        self._device_type = device_type
        self._app_version = app_version
        self._system_name = system_name
        self._system_version = system_version
        self._system_model = system_model

    def get_device_details(self, version: Optional[str] = None) -> DeviceDetails:
        return DeviceDetails(
            device=self._device_type,
            app_version=version or self._app_version,
            system_name=self._system_name,
            system_version=self._system_version,
            system_model=self._system_model or "System Product Name",
        )

    @property
    def device_type(self) -> DeviceType:
        return self._device_type


class DeviceConfigurationFactory:
    """Factory class for creating device configurations."""

    _DEVICE_CONFIGS: Dict[DeviceType, type[DeviceConfigurationStrategy]] = {
        DeviceType.DESKTOPWIN: DesktopWindowsConfig,
        DeviceType.DESKTOPMAC: DesktopMacConfig,
        DeviceType.CHROMEOS: ChromeOSConfig,
        DeviceType.ANDROID: AndroidConfig,
        DeviceType.ANDROIDSECONDARY: AndroidSecondaryConfig,
        DeviceType.IOS: iOSConfig,
        DeviceType.IOSIPAD: iPadConfig,
        DeviceType.WATCHOS: WatchOSConfig,
        DeviceType.WEAROS: WearOSConfig,
        DeviceType.VISIONOS: VisionOSConfig,
    }

    # V3 token support matching TypeScript TOKEN_V3_SUPPORT
    _V3_SUPPORTED_DEVICES = {
        DeviceType.DESKTOPWIN,
        DeviceType.DESKTOPMAC,
        DeviceType.CHROMEOS,
    }

    # Sync support matching TypeScript SYNC_SUPPORT
    _SYNC_SUPPORTED_DEVICES = {
        DeviceType.IOS,
        DeviceType.IOSIPAD,
        DeviceType.ANDROID,
        DeviceType.CHROMEOS,
        DeviceType.DESKTOPWIN,
        DeviceType.DESKTOPMAC,
    }

    @classmethod
    def create_config(
        cls, device_type: Union[DeviceType, str]
    ) -> DeviceConfigurationStrategy:
        """Create a device configuration strategy for the specified device type."""
        if isinstance(device_type, str):
            try:
                device_type = DeviceType(device_type)
            except ValueError:
                raise ValueError(f"Unsupported device type: {device_type}")

        config_class = cls._DEVICE_CONFIGS.get(device_type)
        if not config_class:
            raise ValueError(
                f"No configuration available for device type: {device_type}"
            )

        return config_class()

    @classmethod
    def create_custom_config(
        cls,
        device_type: Union[DeviceType, str],
        app_version: str,
        system_name: str,
        system_version: str,
        system_model: Optional[str] = None,
    ) -> CustomDeviceConfig:
        """Create a custom device configuration."""
        if isinstance(device_type, str):
            try:
                device_type = DeviceType(device_type)
            except ValueError:
                raise ValueError(f"Unsupported device type: {device_type}")

        return CustomDeviceConfig(
            device_type, app_version, system_name, system_version, system_model
        )

    @classmethod
    def get_supported_devices(cls) -> List[DeviceType]:
        """Get list of supported device types."""
        return list(cls._DEVICE_CONFIGS.keys())

    @classmethod
    def is_v3_token_supported(cls, device_type: Union[DeviceType, str]) -> bool:
        """Check if device type supports V3 tokens."""
        if isinstance(device_type, str):
            device_type = DeviceType(device_type)

        return device_type in cls._V3_SUPPORTED_DEVICES

    @classmethod
    def is_sync_supported(cls, device_type: Union[DeviceType, str]) -> bool:
        """Check if device type supports sync."""
        if isinstance(device_type, str):
            device_type = DeviceType(device_type)

        return device_type in cls._SYNC_SUPPORTED_DEVICES


# Convenience functions matching TypeScript interface
def get_device_details(
    device: Union[DeviceType, str], version: Optional[str] = None
) -> Optional[DeviceDetails]:
    """
    Get device details for a specific device type.
    Matches TypeScript getDeviceDetails function interface.

    Args:
        device: The device type to get details for
        version: Optional app version override

    Returns:
        DeviceDetails object or None if device type is not supported
    """
    try:
        config = DeviceConfigurationFactory.create_config(device)
        return config.get_device_details(version)
    except ValueError:
        return None


def is_v3_supported(device: Union[DeviceType, str]) -> bool:
    """
    Check if device supports V3 tokens.
    Matches TypeScript isV3Support function interface.
    """
    return DeviceConfigurationFactory.is_v3_token_supported(device)
