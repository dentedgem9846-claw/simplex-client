"""Pydantic type definitions for the SimpleX Chat API."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag


# ---------------------------------------------------------------------------
# Config shared by all models
# ---------------------------------------------------------------------------

class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ChatType(str, Enum):
    direct = "direct"
    group = "group"
    local = "local"


class CIDeleteMode(str, Enum):
    broadcast = "broadcast"
    internal = "internal"
    internal_mark = "internalMark"


class GroupMemberRole(str, Enum):
    observer = "observer"
    author = "author"
    member = "member"
    moderator = "moderator"
    admin = "admin"
    owner = "owner"


class GroupMemberStatus(str, Enum):
    rejected = "rejected"
    removed = "removed"
    left = "left"
    deleted = "deleted"
    unknown = "unknown"
    invited = "invited"
    pending_approval = "pending_approval"
    pending_review = "pending_review"
    introduced = "introduced"
    intro_inv = "intro-inv"
    accepted = "accepted"
    announced = "announced"
    connected = "connected"
    complete = "complete"
    creator = "creator"


class GroupMemberCategory(str, Enum):
    user = "user"
    invitee = "invitee"
    host = "host"
    pre = "pre"
    post = "post"


class ContactStatus(str, Enum):
    active = "active"
    deleted = "deleted"
    deleted_by_user = "deletedByUser"


class ConnStatus(str, Enum):
    new = "new"
    prepared = "prepared"
    joined = "joined"
    requested = "requested"
    accepted = "accepted"
    snd_ready = "snd-ready"
    ready = "ready"
    conn_deleted = "deleted"


class ConnType(str, Enum):
    contact = "contact"
    member = "member"
    user_contact = "user_contact"


class FileProtocol(str, Enum):
    smp = "smp"
    xftp = "xftp"
    local = "local"


class FeatureAllowed(str, Enum):
    always = "always"
    yes = "yes"
    no = "no"


class ReportReason(str, Enum):
    spam = "spam"
    content = "content"
    community = "community"
    profile = "profile"
    other = "other"


# ---------------------------------------------------------------------------
# Shared / small types
# ---------------------------------------------------------------------------

class CreatedConnLink(_Base):
    conn_full_link: str = Field(alias="connFullLink")
    conn_short_link: str | None = Field(default=None, alias="connShortLink")

    def __str__(self) -> str:
        return self.conn_short_link or self.conn_full_link


class CryptoFileArgs(_Base):
    file_key: str = Field(alias="fileKey")
    file_nonce: str = Field(alias="fileNonce")


class CryptoFile(_Base):
    file_path: str = Field(alias="filePath")
    crypto_args: CryptoFileArgs | None = Field(default=None, alias="cryptoArgs")


class VersionRange(_Base):
    min_version: int = Field(alias="minVersion")
    max_version: int = Field(alias="maxVersion")


# ---------------------------------------------------------------------------
# Profile / User types
# ---------------------------------------------------------------------------

class Profile(_Base):
    display_name: str = Field(alias="displayName")
    full_name: str = Field(default="", alias="fullName")
    short_descr: str | None = Field(default=None, alias="shortDescr")
    image: str | None = None
    contact_link: str | None = Field(default=None, alias="contactLink")
    preferences: dict[str, Any] | None = None
    peer_type: str | None = Field(default=None, alias="peerType")


class LocalProfile(Profile):
    profile_id: int = Field(alias="profileId")
    local_alias: str = Field(default="", alias="localAlias")


class User(_Base):
    user_id: int = Field(alias="userId")
    agent_user_id: int = Field(alias="agentUserId")
    user_contact_id: int = Field(alias="userContactId")
    local_display_name: str = Field(alias="localDisplayName")
    profile: LocalProfile
    active_user: bool = Field(alias="activeUser")
    active_order: int = Field(alias="activeOrder")
    show_ntfs: bool = Field(default=True, alias="showNtfs")
    send_rcpts_contacts: bool = Field(default=False, alias="sendRcptsContacts")
    send_rcpts_small_groups: bool = Field(default=False, alias="sendRcptsSmallGroups")


class UserInfo(_Base):
    user: User
    unread_count: int = Field(alias="unreadCount")


class NewUser(_Base):
    profile: Profile | None = None
    past_timestamp: bool = Field(default=False, alias="pastTimestamp")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

class Connection(_Base):
    conn_id: int = Field(alias="connId")
    agent_conn_id: str = Field(alias="agentConnId")
    conn_chat_version: int = Field(default=0, alias="connChatVersion")
    conn_type: str = Field(default="contact", alias="connType")
    conn_status: str = Field(default="new", alias="connStatus")
    pq_support: bool = Field(default=False, alias="pqSupport")
    pq_encryption: bool = Field(default=False, alias="pqEncryption")


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

class ChatSettings(_Base):
    enable_ntfs: str | None = Field(default=None, alias="enableNtfs")
    send_rcpts: bool | None = Field(default=None, alias="sendRcpts")
    fav: bool = Field(default=False, alias="favorite")


class Contact(_Base):
    contact_id: int = Field(alias="contactId")
    local_display_name: str = Field(alias="localDisplayName")
    profile: LocalProfile
    active_conn: Connection | None = Field(default=None, alias="activeConn")
    via_group: int | None = Field(default=None, alias="viaGroup")
    contact_used: bool = Field(default=False, alias="contactUsed")
    contact_status: ContactStatus = Field(default=ContactStatus.active, alias="contactStatus")
    chat_settings: ChatSettings = Field(alias="chatSettings")
    contact_grp_inv_sent: bool = Field(default=False, alias="contactGrpInvSent")
    chat_deleted: bool = Field(default=False, alias="chatDeleted")
    created_at: str = Field(default="", alias="createdAt")
    updated_at: str = Field(default="", alias="updatedAt")


class UserContactRequest(_Base):
    contact_request_id: int = Field(alias="contactRequestId")
    local_display_name: str = Field(alias="localDisplayName")
    profile: Profile
    pq_support: bool = Field(default=False, alias="pqSupport")
    created_at: str = Field(default="", alias="createdAt")
    updated_at: str = Field(default="", alias="updatedAt")


# ---------------------------------------------------------------------------
# Address
# ---------------------------------------------------------------------------

class AutoAccept(_Base):
    accept_incognito: bool = Field(default=False, alias="acceptIncognito")


class AddressSettings(_Base):
    business_address: bool = Field(default=False, alias="businessAddress")
    auto_accept: AutoAccept | None = Field(default=None, alias="autoAccept")
    auto_reply: dict[str, Any] | None = Field(default=None, alias="autoReply")


class UserContactLink(_Base):
    user_contact_link_id: int = Field(alias="userContactLinkId")
    conn_link_contact: CreatedConnLink = Field(alias="connLinkContact")
    short_link_data_set: bool = Field(default=False, alias="shortLinkDataSet")
    short_link_large_data_set: bool = Field(default=False, alias="shortLinkLargeDataSet")
    address_settings: AddressSettings = Field(alias="addressSettings")

    @property
    def contact_link(self) -> str:
        return str(self.conn_link_contact)


# ---------------------------------------------------------------------------
# Group types
# ---------------------------------------------------------------------------

class GroupProfile(_Base):
    display_name: str = Field(alias="displayName")
    full_name: str = Field(default="", alias="fullName")
    short_descr: str | None = Field(default=None, alias="shortDescr")
    description: str | None = None
    image: str | None = None
    group_preferences: dict[str, Any] | None = Field(default=None, alias="groupPreferences")


class GroupSupportChat(_Base):
    unread_count: int = Field(default=0, alias="unreadCount")
    unread_mention: bool = Field(default=False, alias="unreadMention")
    last_msg_time: str | None = Field(default=None, alias="lastMsgTime")


class GroupMember(_Base):
    group_member_id: int = Field(alias="groupMemberId")
    group_id: int = Field(alias="groupId")
    member_id: str = Field(alias="memberId")
    member_role: GroupMemberRole = Field(alias="memberRole")
    member_category: GroupMemberCategory = Field(alias="memberCategory")
    member_status: GroupMemberStatus = Field(alias="memberStatus")
    blocked_by_admin: bool = Field(default=False, alias="blockedByAdmin")
    local_display_name: str = Field(alias="localDisplayName")
    member_profile: LocalProfile = Field(alias="memberProfile")
    member_contact_id: int | None = Field(default=None, alias="memberContactId")
    member_contact_profile_id: int = Field(alias="memberContactProfileId")
    active_conn: Connection | None = Field(default=None, alias="activeConn")
    created_at: str = Field(default="", alias="createdAt")
    updated_at: str = Field(default="", alias="updatedAt")


class GroupInfo(_Base):
    group_id: int = Field(alias="groupId")
    local_display_name: str = Field(alias="localDisplayName")
    group_profile: GroupProfile = Field(alias="groupProfile")
    local_alias: str = Field(default="", alias="localAlias")
    membership: GroupMember
    chat_settings: ChatSettings = Field(alias="chatSettings")
    members_require_attention: int = Field(default=0, alias="membersRequireAttention")
    created_at: str = Field(default="", alias="createdAt")
    updated_at: str = Field(default="", alias="updatedAt")


class GroupLink(_Base):
    user_contact_link_id: int = Field(alias="userContactLinkId")
    conn_link_contact: CreatedConnLink = Field(alias="connLinkContact")
    short_link_data_set: bool = Field(default=False, alias="shortLinkDataSet")
    short_link_large_data_set: bool = Field(default=False, alias="shortLinkLargeDataSet")
    group_link_id: str = Field(alias="groupLinkId")
    accept_member_role: GroupMemberRole = Field(alias="acceptMemberRole")


class GroupSummary(_Base):
    current_members: int = Field(alias="currentMembers")


class GroupInfoSummary(_Base):
    group_info: GroupInfo = Field(alias="groupInfo")
    group_summary: GroupSummary = Field(alias="groupSummary")


# ---------------------------------------------------------------------------
# MsgContent discriminated union
# ---------------------------------------------------------------------------

class MsgContentText(_Base):
    type: Literal["text"] = "text"
    text: str


class MsgContentLink(_Base):
    type: Literal["link"] = "link"
    text: str
    preview: dict[str, Any] = {}


class MsgContentImage(_Base):
    type: Literal["image"] = "image"
    text: str
    image: str


class MsgContentVideo(_Base):
    type: Literal["video"] = "video"
    text: str
    image: str
    duration: int


class MsgContentVoice(_Base):
    type: Literal["voice"] = "voice"
    text: str
    duration: int


class MsgContentFile(_Base):
    type: Literal["file"] = "file"
    text: str


class MsgContentUnknown(_Base):
    type: str = "unknown"
    tag: str = ""
    text: str = ""
    extra_json: dict[str, Any] = Field(default={}, alias="json")


def _get_msg_content_discriminator(v: Any) -> str:
    if isinstance(v, dict):
        t = v.get("type", "unknown")
        if t in ("text", "link", "image", "video", "voice", "file"):
            return t
        return "unknown"
    return getattr(v, "type", "unknown")


MsgContent = Annotated[
    Annotated[MsgContentText, Tag("text")]
    | Annotated[MsgContentLink, Tag("link")]
    | Annotated[MsgContentImage, Tag("image")]
    | Annotated[MsgContentVideo, Tag("video")]
    | Annotated[MsgContentVoice, Tag("voice")]
    | Annotated[MsgContentFile, Tag("file")]
    | Annotated[MsgContentUnknown, Tag("unknown")],
    Discriminator(_get_msg_content_discriminator),
]


# ---------------------------------------------------------------------------
# Composed / Updated message
# ---------------------------------------------------------------------------

class ComposedMessage(_Base):
    file_source: CryptoFile | None = Field(default=None, alias="fileSource")
    quoted_item_id: int | None = Field(default=None, alias="quotedItemId")
    msg_content: dict[str, Any] = Field(alias="msgContent")
    mentions: dict[str, int] = {}


class UpdatedMessage(_Base):
    msg_content: dict[str, Any] = Field(alias="msgContent")
    mentions: dict[str, int] = {}


# ---------------------------------------------------------------------------
# ChatRef helper
# ---------------------------------------------------------------------------

class ChatRef(_Base):
    chat_type: ChatType = Field(alias="chatType")
    chat_id: int = Field(alias="chatId")

    _PREFIX = {ChatType.direct: "@", ChatType.group: "#", ChatType.local: "*"}

    def __str__(self) -> str:
        return f"{self._PREFIX.get(self.chat_type, '@')}{self.chat_id}"


# ---------------------------------------------------------------------------
# Chat item types
# ---------------------------------------------------------------------------

class FormattedText(_Base):
    text: str
    format: dict[str, Any] | None = None


class CIMeta(_Base):
    item_id: int = Field(alias="itemId")
    item_ts: str = Field(alias="itemTs")
    item_text: str = Field(alias="itemText")
    item_status: dict[str, Any] = Field(alias="itemStatus")
    item_edited: bool = Field(default=False, alias="itemEdited")
    item_live: bool | None = Field(default=None, alias="itemLive")
    user_mention: bool = Field(default=False, alias="userMention")
    deletable: bool = Field(default=False)
    editable: bool = Field(default=False)
    created_at: str = Field(default="", alias="createdAt")
    updated_at: str = Field(default="", alias="updatedAt")


class CIContent(_Base):
    type: str
    text: str = ""
    msg_content: dict[str, Any] | None = Field(default=None, alias="msgContent")


class CIFile(_Base):
    file_id: int = Field(alias="fileId")
    file_name: str = Field(alias="fileName")
    file_size: int = Field(alias="fileSize")
    file_source: CryptoFile | None = Field(default=None, alias="fileSource")
    file_status: str = Field(alias="fileStatus")
    file_protocol: str = Field(alias="fileProtocol")


class CITimed(_Base):
    ttl: int
    delete_at: str | None = Field(default=None, alias="deleteAt")


class CIQuote(_Base):
    item_id: int | None = Field(default=None, alias="itemId")
    sent_at: str = Field(default="", alias="sentAt")
    content: dict[str, Any] = {}
    formatted_text: list[FormattedText] | None = Field(default=None, alias="formattedText")


class CIReactionCount(_Base):
    reaction: dict[str, Any]
    user_reacted: bool = Field(alias="userReacted")
    total_reacted: int = Field(alias="totalReacted")


class CIMention(_Base):
    member_id: str | None = Field(default=None, alias="memberId")
    member_ref: dict[str, Any] | None = Field(default=None, alias="memberRef")


class ChatItem(_Base):
    chat_dir: dict[str, Any] = Field(alias="chatDir")
    meta: CIMeta
    content: CIContent
    mentions: dict[str, CIMention] = {}
    formatted_text: list[FormattedText] | None = Field(default=None, alias="formattedText")
    quoted_item: CIQuote | None = Field(default=None, alias="quotedItem")
    reactions: list[CIReactionCount] = []
    file: CIFile | None = None


class ChatInfo(_Base):
    type: str
    contact: Contact | None = None
    group_info: GroupInfo | None = Field(default=None, alias="groupInfo")


class AChatItem(_Base):
    chat_info: ChatInfo = Field(alias="chatInfo")
    chat_item: ChatItem = Field(alias="chatItem")


class ChatItemDeletion(_Base):
    deleted_chat_item: AChatItem = Field(alias="deletedChatItem")
    to_chat_item: AChatItem | None = Field(default=None, alias="toChatItem")


# ---------------------------------------------------------------------------
# MsgReaction
# ---------------------------------------------------------------------------

class MsgReaction(_Base):
    type: str
    emoji: str | None = None


# ---------------------------------------------------------------------------
# File transfer types
# ---------------------------------------------------------------------------

class FileInvitation(_Base):
    file_name: str = Field(alias="fileName")
    file_size: int = Field(alias="fileSize")
    file_conn_req: str | None = Field(default=None, alias="fileConnReq")


class FileTransferMeta(_Base):
    file_id: int = Field(alias="fileId")
    file_name: str = Field(alias="fileName")
    file_path: str = Field(alias="filePath")
    file_size: int = Field(alias="fileSize")
    chunk_size: int = Field(alias="chunkSize")
    cancelled: bool = False


class RcvFileTransfer(_Base):
    file_id: int = Field(alias="fileId")
    file_invitation: FileInvitation = Field(alias="fileInvitation")
    file_status: str = Field(alias="fileStatus")
    sender_display_name: str = Field(alias="senderDisplayName")
    chunk_size: int = Field(alias="chunkSize")
    cancelled: bool = False


class RcvFileDescr(_Base):
    file_descr_id: int = Field(alias="fileDescrId")
    file_descr_text: str = Field(alias="fileDescrText")
    file_descr_part_no: int = Field(alias="fileDescrPartNo")
    file_descr_complete: bool = Field(alias="fileDescrComplete")


# ---------------------------------------------------------------------------
# ChatError
# ---------------------------------------------------------------------------

class ChatErrorType(_Base):
    type: str


class ChatError(_Base):
    type: str
    error_type: ChatErrorType | None = Field(default=None, alias="errorType")
    agent_error: dict[str, Any] | None = Field(default=None, alias="agentError")
    store_error: dict[str, Any] | None = Field(default=None, alias="storeError")


# ---------------------------------------------------------------------------
# ConnectionPlan
# ---------------------------------------------------------------------------

class ConnectionPlan(_Base):
    type: str
    connection_plan: dict[str, Any] | None = Field(default=None, alias="connectionPlan")
