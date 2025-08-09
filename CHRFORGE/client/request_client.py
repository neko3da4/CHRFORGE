# -*- coding: utf-8 -*-
"""
Request client module for CHRFORGE client.
Provides HTTP request handling with thrift protocol support.
Matches the TypeScript RequestClient interface and functionality.
"""

from __future__ import annotations
import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from CHRFORGE.client.base_client import BaseClient, InternalError


@dataclass
class ParsedThrift:
    """Data class representing parsed thrift response."""

    data: Dict[str, Any]
    method_name: str
    success: bool = True

    def __post_init__(self):
        """Set success based on data content."""
        if not self.data.get("success") and self.data.get("e"):
            self.success = False


class RequestClient:
    """
    Request client for making HTTP requests to LINE API.
    Matches the TypeScript RequestClient class interface and functionality.
    """

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
    SQUARE_ENDPOINTS = {"/SQ1", "/SQLV1"}

    def __init__(self, client: BaseClient):
        """
        Initialize RequestClient.

        Args:
            client: The base client instance
        """
        self.client = client
        self.device_details = client.device_details
        self.endpoint = client.endpoint or "legy.line-apps.com"

        # Generate system type string matching TypeScript format
        self.system_type = (
            f"{self.device_details.device.value}\t{self.device_details.app_version}\t"
            f"{self.device_details.system_name}\t{self.device_details.system_version}"
        )

        # Generate user agent matching TypeScript format
        self.user_agent = f"Line/{self.device_details.app_version}"

    async def request(
        self,
        value: List[Any],
        method_name: str,
        protocol_type: int = 3,
        parse: Union[bool, str] = True,
        path: str = "/S3",
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Any:
        """
        Make a request to LINE API.

        Args:
            value: The thrift value (argument) to request
            method_name: The method name of the request
            protocol_type: The protocol type of the request (default: 3)
            parse: Whether to parse the response (default: True)
            path: The path of the request (default: "/S3")
            headers: Additional headers for the request
            timeout: Request timeout in milliseconds

        Returns:
            The response data

        Raises:
            InternalError: If the request fails
        """
        if timeout is None:
            timeout = self.client.timeout

        response = await self._request_core(
            path=path,
            value=value,
            method_name=method_name,
            protocol_type=protocol_type,
            append_headers=headers or {},
            override_method="POST",
            parse=parse,
            is_re_request=False,
            timeout=timeout,
        )

        return response.data.get("success")

    async def _request_core(
        self,
        path: str,
        value: List[Any],
        method_name: str,
        protocol_type: int,
        append_headers: Dict[str, str],
        override_method: str = "POST",
        parse: Union[bool, str] = True,
        is_re_request: bool = False,
        timeout: int = 30000,
    ) -> ParsedThrift:
        """
        Core request implementation matching TypeScript requestCore method.

        Args:
            path: API endpoint path
            value: Thrift value to send
            method_name: Method name for thrift
            protocol_type: Protocol type for thrift
            append_headers: Additional headers
            override_method: HTTP method
            parse: Parse response flag
            is_re_request: Is this a retry request
            timeout: Request timeout in milliseconds

        Returns:
            ParsedThrift response

        Raises:
            InternalError: If request fails
        """
        # Get protocol handler (this would need to be implemented based on your thrift setup)
        protocol = self._get_protocol(protocol_type)

        # Generate headers
        headers = {**self.get_header(override_method), **append_headers}

        # Log request details
        self.client.log(
            "writeThrift",
            {
                "value": value,
                "method_name": method_name,
                "protocol_type": protocol_type,
            },
        )

        # Write thrift request (this would use your thrift implementation)
        thrift_request = self.client.thrift.write_thrift(value, method_name, protocol)

        # Log the actual request
        self.client.log(
            "request",
            {
                "method_name": method_name,
                "path": f"https://{self.endpoint}{path}",
                "method": override_method,
                "headers": headers,
                "timeout": timeout,
                "body": thrift_request,
            },
        )

        # Make HTTP request
        try:
            response = await self.client.fetch(
                f"https://{self.endpoint}{path}",
                {
                    "method": override_method,
                    "headers": headers,
                    "timeout": timeout,
                    "body": thrift_request,
                },
            )
        except asyncio.TimeoutError:
            raise InternalError(
                "RequestTimeout",
                f"Request timeout after {timeout}ms for {method_name}({path})",
            )
        except Exception as e:
            raise InternalError(
                "RequestError", f"Request failed for {method_name}({path}): {str(e)}"
            )

        # Handle next access token
        next_token = getattr(response, "headers", {}).get("x-line-next-access")
        if next_token:
            self.client.emit("update:authtoken", next_token)

        # Get response body
        try:
            if hasattr(response, "content"):
                body = await response.content()
            elif hasattr(response, "read"):
                body = await response.read()
            else:
                body = response

            parsed_body = bytes(body) if isinstance(body, (list, bytearray)) else body
        except Exception as e:
            raise InternalError(
                "RequestError", f"Failed to read response body: {str(e)}"
            )

        # Log response
        self.client.log(
            "response",
            {
                "status": getattr(response, "status", 200),
                "headers": getattr(response, "headers", {}),
                "parsed_body": parsed_body,
                "method_name": method_name,
            },
        )

        # Parse thrift response
        try:
            parsed_response = self.client.thrift.read_thrift(parsed_body, protocol)
        except Exception:
            body_hex = " ".join(
                f"{b:02x}" for b in parsed_body[:100]
            )  # First 100 bytes
            raise InternalError(
                "RequestError",
                f"Request internal failed: Invalid response buffer <{body_hex}>",
            )

        # Create ParsedThrift object
        res = ParsedThrift(data=parsed_response, method_name=method_name)
        has_error = not res.data.get(0) and len(res.data) > 0

        # Process response based on parse parameter
        if parse is True:
            # Use thrift rename_data method
            self.client.thrift.rename_data(res, path in self.SQUARE_ENDPOINTS)
        elif isinstance(parse, str):
            # Custom parsing with specific struct name
            res.data["success"] = self.client.thrift.rename_thrift(
                parse, res.data.get(0)
            )
            if 0 in res.data:
                del res.data[0]
            if res.data.get(1):
                struct_name = self.EXCEPTION_TYPES.get(path, "TalkException")
                res.data["e"] = self.client.thrift.rename_thrift(
                    struct_name, res.data[1]
                )
                del res.data[1]
        else:
            # Basic parsing without renaming
            res.data["success"] = res.data.get(0)
            if 0 in res.data:
                del res.data[0]
            if res.data.get(1):
                struct_name = self.EXCEPTION_TYPES.get(path, "TalkException")
                res.data["e"] = self.client.thrift.rename_thrift(
                    struct_name, res.data[1]
                )
                del res.data[1]

        # Log parsed response
        self.client.log("readThrift", {"res": res})

        # Handle token refresh
        is_refresh = (
            res.data.get("e")
            and res.data["e"].get("code") == "MUST_REFRESH_V3_TOKEN"
            and await self.client.storage.get("refreshToken")
        )

        # Handle errors
        if res.data.get("e") and not is_refresh:
            raise InternalError(
                "RequestError",
                f"Request internal failed, {method_name}({path}) -> {json.dumps(res.data['e'])}",
                res.data["e"],
            )

        if has_error and not is_refresh:
            raise InternalError(
                "RequestError",
                f"Request internal failed, {method_name}({path}) -> {json.dumps(res.data)}",
                res.data,
            )

        # Handle token refresh and retry
        if is_refresh and not is_re_request:
            await self.client.auth.try_refresh_token()
            return await self._request_core(
                path,
                value,
                method_name,
                protocol_type,
                append_headers,
                override_method,
                parse,
                True,
                timeout,
            )

        return res

    def get_header(self, override_method: str = "POST") -> Dict[str, str]:
        """
        Get HTTP headers for a request matching TypeScript getHeader method.

        Args:
            override_method: The HTTP method to use in the x-lhm header

        Returns:
            Dictionary of HTTP headers

        Raises:
            InternalError: If the client has not been setup yet
        """
        headers = {
            "Host": self.endpoint,
            "accept": "application/x-thrift",
            "user-agent": self.user_agent,
            "x-line-application": self.system_type,
            "content-type": "application/x-thrift",
            "x-lal": "ja_JP",
            "x-lpv": "1",
            "x-lhm": override_method,
            "accept-encoding": "gzip",
        }

        # Add auth token if available
        if self.client.auth_token:
            headers["x-line-access"] = self.client.auth_token

        return headers

    def _get_protocol(self, protocol_type: int) -> Any:
        """
        Get protocol handler for thrift communication.
        This is a placeholder - implement based on your thrift setup.

        Args:
            protocol_type: Protocol type identifier

        Returns:
            Protocol handler object
        """
        # This should be implemented based on your thrift protocol setup
        # For example, you might have a Protocols dictionary like in TypeScript:
        # return Protocols[protocol_type]

        # Placeholder implementation
        return {"type": protocol_type, "name": f"protocol_{protocol_type}"}

    def get_exception_type(self, path: str) -> Optional[str]:
        """Get exception type for endpoint path."""
        return self.EXCEPTION_TYPES.get(path)

    def is_square_endpoint(self, path: str) -> bool:
        """Check if endpoint is a Square endpoint."""
        return path in self.SQUARE_ENDPOINTS

    def __repr__(self) -> str:
        """String representation of RequestClient."""
        return f"RequestClient(endpoint={self.endpoint}, device={self.device_details.device.value})"


class TimeoutSignal:
    """Helper class for handling request timeouts."""

    def __init__(self, timeout_ms: int):
        self.timeout_ms = timeout_ms
        self.is_cancelled = False

    async def __aenter__(self):
        """Async context manager entry."""
        if self.timeout_ms > 0:
            self.task = asyncio.create_task(self._timeout())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.is_cancelled = True
        if hasattr(self, "task") and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _timeout(self):
        """Internal timeout handler."""
        try:
            await asyncio.sleep(self.timeout_ms / 1000.0)
            if not self.is_cancelled:
                raise asyncio.TimeoutError(
                    f"Request timed out after {self.timeout_ms}ms"
                )
        except asyncio.CancelledError:
            pass

    @staticmethod
    def timeout(timeout_ms: int):
        """Create timeout signal for the given milliseconds."""
        return TimeoutSignal(timeout_ms)


# Additional helper functions for thrift protocol management
class ProtocolRegistry:
    """Registry for thrift protocols."""

    def __init__(self):
        self._protocols: Dict[int, Any] = {}

    def register_protocol(self, protocol_id: int, protocol_handler: Any) -> None:
        """Register a protocol handler."""
        self._protocols[protocol_id] = protocol_handler

    def get_protocol(self, protocol_id: int) -> Any:
        """Get protocol handler by ID."""
        protocol = self._protocols.get(protocol_id)
        if not protocol:
            raise ValueError(f"Unknown protocol ID: {protocol_id}")
        return protocol

    def get_supported_protocols(self) -> List[int]:
        """Get list of supported protocol IDs."""
        return list(self._protocols.keys())


# Global protocol registry instance
_protocol_registry = ProtocolRegistry()


def get_protocol_registry() -> ProtocolRegistry:
    """Get the global protocol registry instance."""
    return _protocol_registry


def register_protocol(protocol_id: int, protocol_handler: Any) -> None:
    """Register a protocol handler globally."""
    _protocol_registry.register_protocol(protocol_id, protocol_handler)
