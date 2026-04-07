"""Event definitions for the SimpleX Chat API.

Events are unsolicited messages from the CLI (no corrId).
All events use ``type`` as a discriminator tag.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import ConfigDict, Field

from .types import (
    AChatItem,
    ChatError,
    ChatItemDeletion,
    Contact,
    FileTransferMeta,
    GroupInfo,
    GroupMember,
    MsgReaction,
    RcvFileDescr,
    RcvFileTransfer,
    User,
    UserContactRequest,
    _Base,
)

# ---------------------------------------------------------------------------
# Base event
# ---------------------------------------------------------------------------


class Event(_Base):
    """Base for all events. Unknown fields are silently ignored."""

    model_config = ConfigDict(extra="ignore")
    type: str


# ---------------------------------------------------------------------------
# Contact / connection events
# ---------------------------------------------------------------------------


class ContactConnectedEvent(Event):
    type: str = "contactConnected"
    user: User
    contact: Contact


class ContactUpdatedEvent(Event):
    type: str = "contactUpdated"
    user: User
    from_contact: Contact = Field(alias="fromContact")
    to_contact: Contact = Field(alias="toContact")


class ContactDeletedByContactEvent(Event):
    type: str = "contactDeletedByContact"
    user: User
    contact: Contact


class ReceivedContactRequestEvent(Event):
    type: str = "receivedContactRequest"
    user: User
    contact_request: UserContactRequest = Field(alias="contactRequest")


class ContactSndReadyEvent(Event):
    type: str = "contactSndReady"
    user: User
    contact: Contact


class AcceptingContactRequestEvent(Event):
    type: str = "acceptingContactRequest"
    user: User
    contact: Contact


class ContactConnectingEvent(Event):
    type: str = "contactConnecting"
    user: User
    contact: Contact


# ---------------------------------------------------------------------------
# Message events
# ---------------------------------------------------------------------------


class NewChatItemsEvent(Event):
    type: str = "newChatItems"
    user: User
    chat_items: list[AChatItem] = Field(alias="chatItems")


class ChatItemUpdatedEvent(Event):
    type: str = "chatItemUpdated"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")


class ChatItemsDeletedEvent(Event):
    type: str = "chatItemsDeleted"
    user: User
    chat_item_deletions: list[ChatItemDeletion] = Field(alias="chatItemDeletions")
    by_user: bool = Field(default=False, alias="byUser")
    timed: bool = False


class ChatItemReactionEvent(Event):
    type: str = "chatItemReaction"
    user: User
    added: bool
    reaction: MsgReaction


class ChatItemsStatusesUpdatedEvent(Event):
    type: str = "chatItemsStatusesUpdated"
    user: User
    chat_items: list[AChatItem] = Field(alias="chatItems")


# ---------------------------------------------------------------------------
# Group events
# ---------------------------------------------------------------------------


class ReceivedGroupInvitationEvent(Event):
    type: str = "receivedGroupInvitation"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    contact: Contact
    member_role: str = Field(alias="memberRole")


class UserJoinedGroupEvent(Event):
    type: str = "userJoinedGroup"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    host_member: GroupMember = Field(alias="hostMember")


class GroupUpdatedEvent(Event):
    type: str = "groupUpdated"
    user: User
    from_group: GroupInfo = Field(alias="fromGroup")
    to_group: GroupInfo = Field(alias="toGroup")


class JoinedGroupMemberEvent(Event):
    type: str = "joinedGroupMember"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    member: GroupMember


class MemberRoleEvent(Event):
    type: str = "memberRole"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    by_member: GroupMember = Field(alias="byMember")
    member: GroupMember
    from_role: str = Field(alias="fromRole")
    to_role: str = Field(alias="toRole")


class DeletedMemberEvent(Event):
    type: str = "deletedMember"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    by_member: GroupMember = Field(alias="byMember")
    deleted_member: GroupMember = Field(alias="deletedMember")


class LeftMemberEvent(Event):
    type: str = "leftMember"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    member: GroupMember


class DeletedMemberUserEvent(Event):
    type: str = "deletedMemberUser"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    member: GroupMember


class GroupDeletedEvent(Event):
    type: str = "groupDeleted"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    member: GroupMember


class ConnectedToGroupMemberEvent(Event):
    type: str = "connectedToGroupMember"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    member: GroupMember


class MemberBlockedForAllEvent(Event):
    type: str = "memberBlockedForAll"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    by_member: GroupMember = Field(alias="byMember")
    member: GroupMember
    blocked: bool


class GroupMemberUpdatedEvent(Event):
    type: str = "groupMemberUpdated"
    user: User
    group_info: GroupInfo = Field(alias="groupInfo")
    from_member: GroupMember = Field(alias="fromMember")
    to_member: GroupMember = Field(alias="toMember")


# ---------------------------------------------------------------------------
# File events
# ---------------------------------------------------------------------------


class RcvFileDescrReadyEvent(Event):
    type: str = "rcvFileDescrReady"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")
    rcv_file_transfer: RcvFileTransfer = Field(alias="rcvFileTransfer")
    rcv_file_descr: RcvFileDescr = Field(alias="rcvFileDescr")


class RcvFileCompleteEvent(Event):
    type: str = "rcvFileComplete"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")


class SndFileCompleteXFTPEvent(Event):
    type: str = "sndFileCompleteXFTP"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")
    file_transfer_meta: FileTransferMeta = Field(alias="fileTransferMeta")


class RcvFileStartEvent(Event):
    type: str = "rcvFileStart"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")


class RcvFileSndCancelledEvent(Event):
    type: str = "rcvFileSndCancelled"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")
    rcv_file_transfer: RcvFileTransfer = Field(alias="rcvFileTransfer")


class RcvFileAcceptedEvent(Event):
    type: str = "rcvFileAccepted"
    user: User
    chat_item: AChatItem = Field(alias="chatItem")


class RcvFileErrorEvent(Event):
    type: str = "rcvFileError"
    user: User
    agent_error: dict[str, Any] = Field(alias="agentError")
    rcv_file_transfer: RcvFileTransfer = Field(alias="rcvFileTransfer")


class SndFileErrorEvent(Event):
    type: str = "sndFileError"
    user: User
    file_transfer_meta: FileTransferMeta = Field(alias="fileTransferMeta")
    error_message: str = Field(alias="errorMessage")


# ---------------------------------------------------------------------------
# Error / system events
# ---------------------------------------------------------------------------


class MessageErrorEvent(Event):
    type: str = "messageError"
    user: User
    severity: str
    error_message: str = Field(alias="errorMessage")


class ChatErrorEvent(Event):
    type: str = "chatError"
    chat_error: ChatError = Field(alias="chatError")


class ChatErrorsEvent(Event):
    type: str = "chatErrors"
    chat_errors: list[ChatError] = Field(alias="chatErrors")


# ---------------------------------------------------------------------------
# Event type registry
# ---------------------------------------------------------------------------

EVENT_TYPES: dict[str, type[Event]] = {
    "contactConnected": ContactConnectedEvent,
    "contactUpdated": ContactUpdatedEvent,
    "contactDeletedByContact": ContactDeletedByContactEvent,
    "receivedContactRequest": ReceivedContactRequestEvent,
    "contactSndReady": ContactSndReadyEvent,
    "acceptingContactRequest": AcceptingContactRequestEvent,
    "contactConnecting": ContactConnectingEvent,
    "newChatItems": NewChatItemsEvent,
    "chatItemUpdated": ChatItemUpdatedEvent,
    "chatItemsDeleted": ChatItemsDeletedEvent,
    "chatItemReaction": ChatItemReactionEvent,
    "chatItemsStatusesUpdated": ChatItemsStatusesUpdatedEvent,
    "receivedGroupInvitation": ReceivedGroupInvitationEvent,
    "userJoinedGroup": UserJoinedGroupEvent,
    "groupUpdated": GroupUpdatedEvent,
    "joinedGroupMember": JoinedGroupMemberEvent,
    "memberRole": MemberRoleEvent,
    "deletedMember": DeletedMemberEvent,
    "leftMember": LeftMemberEvent,
    "deletedMemberUser": DeletedMemberUserEvent,
    "groupDeleted": GroupDeletedEvent,
    "connectedToGroupMember": ConnectedToGroupMemberEvent,
    "memberBlockedForAll": MemberBlockedForAllEvent,
    "groupMemberUpdated": GroupMemberUpdatedEvent,
    "rcvFileDescrReady": RcvFileDescrReadyEvent,
    "rcvFileComplete": RcvFileCompleteEvent,
    "sndFileCompleteXFTP": SndFileCompleteXFTPEvent,
    "rcvFileStart": RcvFileStartEvent,
    "rcvFileSndCancelled": RcvFileSndCancelledEvent,
    "rcvFileAccepted": RcvFileAcceptedEvent,
    "rcvFileError": RcvFileErrorEvent,
    "sndFileError": SndFileErrorEvent,
    "messageError": MessageErrorEvent,
    "chatError": ChatErrorEvent,
    "chatErrors": ChatErrorsEvent,
}


logger = structlog.get_logger(__name__)


def parse_event(data: dict[str, Any]) -> Event:
    """Parse a raw event dict into a typed Event instance.

    Unknown event types are returned as a generic ``Event``.
    """
    event_type = data.get("type", "")
    cls = EVENT_TYPES.get(event_type, Event)
    logger.debug("event.parse", event_type=event_type, known=event_type in EVENT_TYPES)
    return cls.model_validate(data)
