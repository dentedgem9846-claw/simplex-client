"""Command string builders for the SimpleX Chat CLI WebSocket API.

Each function returns the command string to send via ``send_command``.
"""

from __future__ import annotations

import json
import re
from typing import Any


def _validate_str(value: str, name: str) -> str:
    """Reject strings containing newlines or control characters that could
    break the SimpleX CLI command parser."""
    if re.search(r"[\x00-\x1f]", value):
        raise ValueError(f"{name} contains invalid control characters")
    return value


def _validate_role(role: str) -> str:
    _VALID_ROLES = {"observer", "author", "member", "moderator", "admin", "owner"}
    if role not in _VALID_ROLES:
        raise ValueError(f"invalid role: {role!r}")
    return role


def _validate_delete_mode(mode: str) -> str:
    _VALID_MODES = {"broadcast", "internal", "internalMark", "full", "entity", "messages"}
    if mode not in _VALID_MODES:
        raise ValueError(f"invalid delete mode: {mode!r}")
    return mode


# ---------------------------------------------------------------------------
# User / Profile commands
# ---------------------------------------------------------------------------

def show_active_user() -> str:
    return "/user"


def create_active_user(profile: dict[str, Any]) -> str:
    return f"/_create user {json.dumps(profile)}"


def list_users() -> str:
    return "/users"


def set_active_user(user_id: int) -> str:
    return f"/_user {user_id}"


def delete_user(user_id: int, del_smp: bool = True) -> str:
    flag = "on" if del_smp else "off"
    return f"/_delete user {user_id} del_smp={flag}"


def update_profile(user_id: int, profile: dict[str, Any]) -> str:
    return f"/_profile {user_id} {json.dumps(profile)}"


# ---------------------------------------------------------------------------
# Address commands
# ---------------------------------------------------------------------------

def create_address(user_id: int) -> str:
    return f"/_address {user_id}"


def delete_address(user_id: int) -> str:
    return f"/_delete_address {user_id}"


def show_address(user_id: int) -> str:
    return f"/_show_address {user_id}"


def set_profile_address(user_id: int, on: bool = True) -> str:
    flag = "on" if on else "off"
    return f"/_profile_address {user_id} {flag}"


def set_address_settings(user_id: int, settings: dict[str, Any]) -> str:
    return f"/_address_settings {user_id} {json.dumps(settings)}"


# ---------------------------------------------------------------------------
# Connection commands
# ---------------------------------------------------------------------------

def add_contact(user_id: int, incognito: bool = False) -> str:
    inc = " incognito=on" if incognito else ""
    return f"/_connect {user_id}{inc}"


def connect_via_link(user_id: int, link: str) -> str:
    _validate_str(link, "link")
    return f"/connect {link}"



def connect_plan(user_id: int, link: str) -> str:
    _validate_str(link, "link")
    return f"/_connect plan {user_id} {link}"


def accept_contact(contact_req_id: int) -> str:
    return f"/_accept {contact_req_id}"


def reject_contact(contact_req_id: int) -> str:
    return f"/_reject {contact_req_id}"


# ---------------------------------------------------------------------------
# Contact / chat commands
# ---------------------------------------------------------------------------

def list_contacts(user_id: int) -> str:
    return f"/_contacts {user_id}"


def list_groups(user_id: int, search: str | None = None) -> str:
    if search:
        _validate_str(search, "search")
        return f"/_groups {user_id} {search}"
    return "/groups"


def delete_chat(chat_ref: str, mode: str = "full") -> str:
    _validate_str(chat_ref, "chat_ref")
    _validate_delete_mode(mode)
    return f"/_delete {chat_ref} {mode}"


def set_contact_prefs(contact_id: int, prefs: dict[str, Any]) -> str:
    return f"/_set prefs @{contact_id} {json.dumps(prefs)}"


# ---------------------------------------------------------------------------
# Message commands
# ---------------------------------------------------------------------------

def send_messages(
    chat_ref: str,
    composed_messages: list[dict[str, Any]],
    *,
    live: bool = False,
    ttl: int | None = None,
) -> str:
    _validate_str(chat_ref, "chat_ref")
    cmd = f"/_send {chat_ref}"
    if live:
        cmd += " live=on"
    if ttl is not None:
        cmd += f" ttl={ttl}"
    cmd += f" json {json.dumps(composed_messages)}"
    return cmd


def update_chat_item(
    chat_ref: str,
    chat_item_id: int,
    updated_message: dict[str, Any],
    *,
    live: bool = False,
) -> str:
    _validate_str(chat_ref, "chat_ref")
    cmd = f"/_update item {chat_ref} {chat_item_id}"
    if live:
        cmd += " live=on"
    cmd += f" json {json.dumps(updated_message)}"
    return cmd


def delete_chat_items(
    chat_ref: str,
    item_ids: list[int],
    mode: str = "broadcast",
) -> str:
    _validate_str(chat_ref, "chat_ref")
    _validate_delete_mode(mode)
    ids_str = ",".join(str(i) for i in item_ids)
    return f"/_delete item {chat_ref} {ids_str} {mode}"


def delete_member_chat_items(group_id: int, item_ids: list[int]) -> str:
    ids_str = ",".join(str(i) for i in item_ids)
    return f"/_delete member item #{group_id} {ids_str}"


def chat_item_reaction(
    chat_ref: str,
    chat_item_id: int,
    add: bool,
    reaction: dict[str, Any],
) -> str:
    _validate_str(chat_ref, "chat_ref")
    flag = "on" if add else "off"
    return f"/_reaction {chat_ref} {chat_item_id} {flag} {json.dumps(reaction)}"


# ---------------------------------------------------------------------------
# Group commands
# ---------------------------------------------------------------------------

def create_group(
    user_id: int,
    group_profile: dict[str, Any],
    incognito: bool = False,
) -> str:
    inc = " incognito=on" if incognito else ""
    return f"/_group {user_id}{inc} {json.dumps(group_profile)}"



def update_group_profile(group_id: int, group_profile: dict[str, Any]) -> str:
    return f"/_group_profile #{group_id} {json.dumps(group_profile)}"


def add_member(group_id: int, contact_id: int, role: str = "member") -> str:
    _validate_role(role)
    return f"/_add #{group_id} {contact_id} {role}"


def join_group(group_id: int) -> str:
    return f"/_join #{group_id}"


def accept_member(group_id: int, member_id: int, role: str = "member") -> str:
    _validate_role(role)
    return f"/_accept member #{group_id} {member_id} {role}"


def members_role(group_id: int, member_ids: list[int], role: str) -> str:
    _validate_role(role)
    ids_str = ",".join(str(i) for i in member_ids)
    return f"/_member role #{group_id} {ids_str} {role}"


def block_members_for_all(
    group_id: int,
    member_ids: list[int],
    blocked: bool = True,
) -> str:
    ids_str = ",".join(str(i) for i in member_ids)
    flag = "on" if blocked else "off"
    return f"/_block #{group_id} {ids_str} blocked={flag}"


def remove_members(
    group_id: int,
    member_ids: list[int],
    with_messages: bool = False,
) -> str:
    ids_str = ",".join(str(i) for i in member_ids)
    cmd = f"/_remove #{group_id} {ids_str}"
    if with_messages:
        cmd += " messages=on"
    return cmd


def leave_group(group_id: int) -> str:
    return f"/_leave #{group_id}"


def list_members(group_id: int) -> str:
    return f"/_members #{group_id}"


# ---------------------------------------------------------------------------
# Group link commands
# ---------------------------------------------------------------------------

def create_group_link(group_id: int, role: str = "member") -> str:
    _validate_role(role)
    return f"/_create link #{group_id} {role}"


def group_link_member_role(group_id: int, role: str) -> str:
    _validate_role(role)
    return f"/_set link role #{group_id} {role}"


def delete_group_link(group_id: int) -> str:
    return f"/_delete link #{group_id}"


def get_group_link(group_id: int) -> str:
    return f"/_get link #{group_id}"


# ---------------------------------------------------------------------------
# File commands
# ---------------------------------------------------------------------------

def receive_file(
    file_id: int,
    *,
    file_path: str | None = None,
    encrypt: bool | None = None,
    inline: bool | None = None,
) -> str:
    cmd = f"/freceive {file_id}"
    if encrypt is not None:
        cmd += f" encrypt={'on' if encrypt else 'off'}"
    if inline is not None:
        cmd += f" inline={'on' if inline else 'off'}"
    if file_path is not None:
        _validate_str(file_path, "file_path")
        cmd += f" {file_path}"
    return cmd


def cancel_file(file_id: int) -> str:
    return f"/fcancel {file_id}"
