"""simplex_client — Async Python client for the SimpleX Chat CLI WebSocket API."""

from .client import SimplexClient
from .events import Event, parse_event
from .exceptions import SimplexConnectionError, SimplexError
from .types import (
    AChatItem,
    ChatItem,
    ChatRef,
    ChatType,
    Contact,
    GroupInfo,
    GroupMember,
    GroupMemberRole,
    MsgContentText,
    Profile,
    User,
    UserContactLink,
)

__all__ = [
    "SimplexClient",
    "SimplexError",
    "SimplexConnectionError",
    "Event",
    "parse_event",
    "AChatItem",
    "ChatItem",
    "ChatRef",
    "ChatType",
    "Contact",
    "GroupInfo",
    "GroupMember",
    "GroupMemberRole",
    "MsgContentText",
    "Profile",
    "User",
    "UserContactLink",
]
