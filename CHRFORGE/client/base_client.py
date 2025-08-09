# -*- coding: utf-8 -*-
"""
Base client module for CHRFORGE client.
Provides foundational client functionality and error handling.
"""

from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
from urllib.parse import urlparse

from ..config import ClientConfiguration, DeviceDetails


class InternalError(Exception):
    """
    Internal error class for client operations.
    Matches the TypeScript InternalError interface.
    """

    def __init__(self, error_type: str, message: str, details: Any = None):
        self.error_type = error_type
        self.message = message
        self.details = details
        super().__init__(f"{error_type}: {message}")

    def __repr__(self) -> str:
        return f"InternalError(type={self.error_type}, message={self.message}, details={self.details})"


class BaseClient(ABC):
    """
    Abstract base client class providing core functionality.
    Matches the TypeScript BaseClient interface.
    """

    def __init__(self, config: ClientConfiguration):
        self.config = config
        self.auth_token: Optional[str] = None
        self.endpoint: Optional[str] = None
        self.timeout: int = 30000  # 30 seconds in milliseconds
        self.logger = logging.getLogger(self.__class__.__name__)

        # Event handlers
        self._event_handlers: Dict[str, list[Callable]] = {}

    @property
    def device_details(self) -> DeviceDetails:
        """Get device details from configuration."""
        if not self.config.device_details:
            raise ValueError("Device details not configured")
        return self.config.device_details

    @abstractmethod
    async def fetch(self, url: str, options: Dict[str, Any]) -> Any:
        """
        Abstract method for making HTTP requests.
        Must be implemented by concrete client classes.
        """
        pass

    @abstractmethod
    def log(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Abstract method for logging events.
        Must be implemented by concrete client classes.
        """
        pass

    def emit(self, event: str, *args: Any) -> None:
        """Emit an event to registered handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(*args))
                else:
                    handler(*args)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event}: {e}")

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        """Unregister event handler(s)."""
        if event not in self._event_handlers:
            return

        if handler is None:
            # Remove all handlers for this event
            del self._event_handlers[event]
        else:
            # Remove specific handler
            try:
                self._event_handlers[event].remove(handler)
                if not self._event_handlers[event]:
                    del self._event_handlers[event]
            except ValueError:
                pass

    @property
    @abstractmethod
    def thrift(self) -> Any:
        """
        Abstract property for thrift protocol handler.
        Must be implemented by concrete client classes.
        """
        pass

    @property
    @abstractmethod
    def storage(self) -> Any:
        """
        Abstract property for storage interface.
        Must be implemented by concrete client classes.
        """
        pass

    @property
    @abstractmethod
    def auth(self) -> Any:
        """
        Abstract property for authentication handler.
        Must be implemented by concrete client classes.
        """
        pass

    def set_auth_token(self, token: str) -> None:
        """Set authentication token."""
        self.auth_token = token
        self.emit("update:authtoken", token)

    def set_endpoint(self, endpoint: str) -> None:
        """Set API endpoint."""
        self.endpoint = endpoint

    def get_endpoint_host(self) -> str:
        """Get the host part of the endpoint."""
        if not self.endpoint:
            return "legy.line-apps.com"  # Default from TypeScript

        parsed = urlparse(
            f"https://{self.endpoint}"
            if not self.endpoint.startswith("http")
            else self.endpoint
        )
        return parsed.hostname or "legy.line-apps.com"

    def configure_timeout(self, timeout_ms: int) -> None:
        """Configure request timeout in milliseconds."""
        self.timeout = timeout_ms

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"{self.__class__.__name__}(endpoint={self.endpoint}, has_token={bool(self.auth_token)})"


@dataclass
class ClientConfig:
    """Configuration for BaseClient instances."""

    timeout: int = 30000  # 30 seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    log_level: int = logging.INFO
    enable_debug_logging: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")
