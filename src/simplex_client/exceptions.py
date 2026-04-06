"""Exception types for the SimpleX client library."""

from __future__ import annotations

from typing import Any


class SimplexError(Exception):
    """Raised when a SimpleX command returns a chatCmdError response."""

    def __init__(self, message: str, response: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.response = response


class SimplexConnectionError(Exception):
    """Raised when the WebSocket connection fails or is lost."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause
