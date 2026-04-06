"""Async WebSocket client for the SimpleX Chat CLI API."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from collections.abc import Callable, Coroutine
from typing import Any

import websockets
import websockets.asyncio.client

from . import commands as cmd
from .events import EVENT_TYPES, Event, parse_event
from .exceptions import SimplexConnectionError, SimplexError
from .types import (
    AChatItem,
    Contact,
    ConnectionPlan,
    GroupInfo,
    GroupLink,
    GroupMember,
    GroupProfile,
    User,
    UserContactLink,
    UserInfo,
)

logger = logging.getLogger(__name__)

EventCallback = Callable[[Event], Coroutine[Any, Any, None]]


class SimplexClient:
    """Async context manager for the SimpleX Chat CLI WebSocket API.

    Usage::

        async with SimplexClient("localhost", 5225) as client:
            user = await client.get_user()
            ...
    """

    def __init__(self, host: str = "localhost", port: int = 5225) -> None:
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._corr_id = 0
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._event_handlers: dict[str, list[EventCallback]] = {}
        self._listener_task: asyncio.Task[None] | None = None
        self._closed = False

    # -- Context manager -----------------------------------------------------

    async def __aenter__(self) -> SimplexClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # -- Connection ----------------------------------------------------------

    async def connect(self, host: str | None = None, port: int | None = None) -> None:
        """Open the WebSocket connection and start the listener loop."""
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        self.uri = f"ws://{self.host}:{self.port}"
        self._closed = False
        self._ws = await websockets.asyncio.client.connect(self.uri)
        self._listener_task = asyncio.create_task(self._listen())

    async def close(self) -> None:
        """Close the WebSocket connection and cancel the listener."""
        self._closed = True
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
            self._ws = None
        # Reject all pending commands
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(SimplexConnectionError("connection closed"))
        self._pending.clear()

    # -- Reconnection --------------------------------------------------------

    async def connect_with_backoff(self) -> None:
        """Connect with exponential backoff and jitter.  Loops forever."""
        delay = 1.0
        while not self._closed:
            try:
                await self.connect()
                await self._listener_task  # type: ignore[arg-type]
            except (websockets.ConnectionClosed, OSError) as exc:
                logger.warning("Connection lost: %s — reconnecting…", exc)
            except asyncio.CancelledError:
                return
            if self._closed:
                return
            jitter = random.uniform(0, delay * 0.5)
            wait = min(delay + jitter, 30.0)
            logger.info("Reconnecting in %.1fs…", wait)
            await asyncio.sleep(wait)
            delay = min(delay * 2, 30.0)

    # -- Low-level send/receive ----------------------------------------------

    async def send_command(self, command: str) -> dict[str, Any]:
        """Send a command and wait for the correlated response."""
        if self._ws is None:
            raise SimplexConnectionError("not connected")
        self._corr_id += 1
        corr_id = str(self._corr_id)
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[corr_id] = fut
        msg = json.dumps({"corrId": corr_id, "cmd": command})
        try:
            await self._ws.send(msg)
        except Exception as exc:
            self._pending.pop(corr_id, None)
            raise SimplexConnectionError("send failed", exc) from exc
        return await fut

    async def _listen(self) -> None:
        """Background loop: dispatch responses and events."""
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    raw = raw.decode()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from server: %s", raw[:200])
                    continue

                corr_id = data.get("corrId")
                resp = data.get("resp")
                if resp is None:
                    continue

                if corr_id and corr_id in self._pending:
                    fut = self._pending.pop(corr_id)
                    if not fut.done():
                        fut.set_result(resp)
                else:
                    # Unsolicited event
                    await self._dispatch_event(resp)
        except websockets.ConnectionClosed:
            if not self._closed:
                raise
        except asyncio.CancelledError:
            return
        finally:
            # Reject any remaining pending commands
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(
                        SimplexConnectionError("connection closed during listen")
                    )
            self._pending.clear()

    async def _dispatch_event(self, data: dict[str, Any]) -> None:
        event_type = data.get("type", "")
        event = parse_event(data)
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception("Error in event handler for %s", event_type)

    # -- Event registration --------------------------------------------------

    def on_event(
        self, event_type: str, callback: EventCallback | None = None
    ) -> Callable[[EventCallback], EventCallback]:
        """Register an event handler.  Can be used as a decorator::

            @client.on_event("newChatItems")
            async def handle(event):
                ...

        Or called directly::

            client.on_event("newChatItems", my_handler)
        """

        def decorator(fn: EventCallback) -> EventCallback:
            self._event_handlers.setdefault(event_type, []).append(fn)
            return fn

        if callback is not None:
            decorator(callback)
            return decorator
        return decorator

    # -- Run helper ----------------------------------------------------------

    async def run(self) -> None:
        """Convenience: connect with backoff and run until cancelled."""
        await self.connect_with_backoff()

    # -- Helper to raise on chatCmdError ------------------------------------

    def _check_error(self, resp: dict[str, Any]) -> None:
        if resp.get("type") == "chatCmdError":
            chat_error = resp.get("chatError", {})
            error_type = chat_error.get("errorType", {}) if isinstance(chat_error, dict) else {}
            msg = error_type.get("type", "unknown error") if isinstance(error_type, dict) else str(chat_error)
            raise SimplexError(msg, resp)

    # -----------------------------------------------------------------------
    # High-level API methods
    # -----------------------------------------------------------------------

    # -- User / Profile -----------------------------------------------------

    async def get_user(self) -> User | None:
        """Get the active user profile, or ``None`` if none exists."""
        resp = await self.send_command(cmd.show_active_user())
        if resp.get("type") == "activeUser":
            return User.model_validate(resp.get("user", resp))
        if resp.get("type") == "chatCmdError":
            chat_error = resp.get("chatError", {})
            if isinstance(chat_error, dict):
                et = chat_error.get("errorType", {})
                if isinstance(et, dict) and et.get("type") == "noActiveUser":
                    return None
            raise SimplexError("get_user failed", resp)
        return None

    async def create_user(self, display_name: str, full_name: str = "") -> User:
        """Create a new user profile and make it active."""
        profile = {"displayName": display_name, "fullName": full_name}
        resp = await self.send_command(
            cmd.create_active_user({"profile": profile, "pastTimestamp": False})
        )
        self._check_error(resp)
        return User.model_validate(resp.get("user", resp))

    async def list_users(self) -> list[UserInfo]:
        resp = await self.send_command(cmd.list_users())
        self._check_error(resp)
        return [UserInfo.model_validate(u) for u in resp.get("users", [])]

    async def set_active_user(self, user_id: int) -> User:
        resp = await self.send_command(cmd.set_active_user(user_id))
        self._check_error(resp)
        return User.model_validate(resp.get("user", resp))

    async def delete_user(self, user_id: int, del_smp: bool = True) -> None:
        resp = await self.send_command(cmd.delete_user(user_id, del_smp))
        self._check_error(resp)

    async def update_profile(self, user_id: int, profile: dict[str, Any]) -> User:
        resp = await self.send_command(cmd.update_profile(user_id, profile))
        self._check_error(resp)
        return User.model_validate(resp.get("user", resp))

    # -- Address ------------------------------------------------------------

    async def create_address(self, user_id: int) -> UserContactLink:
        resp = await self.send_command(cmd.create_address(user_id))
        self._check_error(resp)
        # Response type is "userContactLinkCreated" with connLinkContact at top level
        if "contactLink" in resp:
            return UserContactLink.model_validate(resp["contactLink"])
        # Build a UserContactLink from the flat response fields
        return UserContactLink.model_validate(resp)

    async def delete_address(self, user_id: int) -> None:
        resp = await self.send_command(cmd.delete_address(user_id))
        self._check_error(resp)

    async def show_address(self, user_id: int) -> UserContactLink | None:
        resp = await self.send_command(cmd.show_address(user_id))
        if resp.get("type") == "userContactLink":
            return UserContactLink.model_validate(resp.get("contactLink", resp))
        self._check_error(resp)
        return None

    async def set_profile_address(self, user_id: int, on: bool = True) -> None:
        resp = await self.send_command(cmd.set_profile_address(user_id, on))
        self._check_error(resp)

    async def set_address_settings(
        self, user_id: int, settings: dict[str, Any]
    ) -> None:
        resp = await self.send_command(cmd.set_address_settings(user_id, settings))
        self._check_error(resp)

    # -- Connection ---------------------------------------------------------

    async def add_contact(self, user_id: int, incognito: bool = False) -> dict[str, Any]:
        resp = await self.send_command(cmd.add_contact(user_id, incognito))
        self._check_error(resp)
        return resp

    async def connect_contact(self, user_id: int, link: str) -> dict[str, Any]:
        resp = await self.send_command(cmd.connect(user_id, link))
        self._check_error(resp)
        return resp

    async def connect_plan(self, user_id: int, link: str) -> ConnectionPlan:
        resp = await self.send_command(cmd.connect_plan(user_id, link))
        self._check_error(resp)
        return ConnectionPlan.model_validate(resp.get("connectionPlan", resp))

    async def accept_contact_request(self, contact_req_id: int) -> dict[str, Any]:
        resp = await self.send_command(cmd.accept_contact(contact_req_id))
        self._check_error(resp)
        return resp

    async def reject_contact_request(self, contact_req_id: int) -> None:
        resp = await self.send_command(cmd.reject_contact(contact_req_id))
        self._check_error(resp)

    # -- Contacts / chats ---------------------------------------------------

    async def list_contacts(self, user_id: int) -> list[Contact]:
        resp = await self.send_command(cmd.list_contacts(user_id))
        self._check_error(resp)
        return [Contact.model_validate(c) for c in resp.get("contacts", [])]

    async def list_groups(
        self, user_id: int, search: str | None = None
    ) -> list[dict[str, Any]]:
        resp = await self.send_command(cmd.list_groups(user_id, search))
        self._check_error(resp)
        return resp.get("groups", [])

    async def delete_chat(self, chat_ref: str, mode: str = "full") -> None:
        resp = await self.send_command(cmd.delete_chat(chat_ref, mode))
        self._check_error(resp)

    async def set_contact_prefs(
        self, contact_id: int, prefs: dict[str, Any]
    ) -> None:
        resp = await self.send_command(cmd.set_contact_prefs(contact_id, prefs))
        self._check_error(resp)

    # -- Messages -----------------------------------------------------------

    async def send_message(
        self,
        chat_ref: str,
        composed_messages: list[dict[str, Any]],
        *,
        live: bool = False,
        ttl: int | None = None,
    ) -> list[AChatItem]:
        resp = await self.send_command(
            cmd.send_messages(chat_ref, composed_messages, live=live, ttl=ttl)
        )
        self._check_error(resp)
        return [AChatItem.model_validate(i) for i in resp.get("chatItems", [])]

    async def update_chat_item(
        self,
        chat_ref: str,
        chat_item_id: int,
        updated_message: dict[str, Any],
        *,
        live: bool = False,
    ) -> dict[str, Any]:
        resp = await self.send_command(
            cmd.update_chat_item(chat_ref, chat_item_id, updated_message, live=live)
        )
        self._check_error(resp)
        return resp

    async def delete_chat_items(
        self,
        chat_ref: str,
        item_ids: list[int],
        mode: str = "broadcast",
    ) -> dict[str, Any]:
        resp = await self.send_command(cmd.delete_chat_item(chat_ref, item_ids, mode))
        self._check_error(resp)
        return resp

    async def delete_member_chat_items(
        self, group_id: int, item_ids: list[int]
    ) -> dict[str, Any]:
        resp = await self.send_command(cmd.delete_member_chat_item(group_id, item_ids))
        self._check_error(resp)
        return resp

    async def react_to_chat_item(
        self,
        chat_ref: str,
        chat_item_id: int,
        add: bool,
        reaction: dict[str, Any],
    ) -> dict[str, Any]:
        resp = await self.send_command(
            cmd.chat_item_reaction(chat_ref, chat_item_id, add, reaction)
        )
        self._check_error(resp)
        return resp

    # -- Groups -------------------------------------------------------------

    async def create_group(
        self, user_id: int, group_profile: dict[str, Any], incognito: bool = False
    ) -> GroupInfo:
        resp = await self.send_command(
            cmd.new_group(user_id, group_profile, incognito)
        )
        self._check_error(resp)
        return GroupInfo.model_validate(resp.get("groupInfo", resp))

    async def update_group_profile(
        self, group_id: int, group_profile: dict[str, Any]
    ) -> GroupInfo:
        resp = await self.send_command(
            cmd.update_group_profile(group_id, group_profile)
        )
        self._check_error(resp)
        return GroupInfo.model_validate(resp.get("toGroup", resp))

    async def add_member(
        self, group_id: int, contact_id: int, role: str = "member"
    ) -> dict[str, Any]:
        resp = await self.send_command(cmd.add_member(group_id, contact_id, role))
        self._check_error(resp)
        return resp

    async def join_group(self, group_id: int) -> dict[str, Any]:
        resp = await self.send_command(cmd.join_group(group_id))
        self._check_error(resp)
        return resp

    async def accept_member(
        self, group_id: int, member_id: int, role: str = "member"
    ) -> dict[str, Any]:
        resp = await self.send_command(cmd.accept_member(group_id, member_id, role))
        self._check_error(resp)
        return resp

    async def set_members_role(
        self, group_id: int, member_ids: list[int], role: str
    ) -> dict[str, Any]:
        resp = await self.send_command(cmd.members_role(group_id, member_ids, role))
        self._check_error(resp)
        return resp

    async def block_members_for_all(
        self, group_id: int, member_ids: list[int], blocked: bool = True
    ) -> dict[str, Any]:
        resp = await self.send_command(
            cmd.block_members_for_all(group_id, member_ids, blocked)
        )
        self._check_error(resp)
        return resp

    async def remove_members(
        self, group_id: int, member_ids: list[int], with_messages: bool = False
    ) -> dict[str, Any]:
        resp = await self.send_command(
            cmd.remove_members(group_id, member_ids, with_messages)
        )
        self._check_error(resp)
        return resp

    async def leave_group(self, group_id: int) -> dict[str, Any]:
        resp = await self.send_command(cmd.leave_group(group_id))
        self._check_error(resp)
        return resp

    async def list_members(self, group_id: int) -> list[GroupMember]:
        resp = await self.send_command(cmd.list_members(group_id))
        self._check_error(resp)
        return [GroupMember.model_validate(m) for m in resp.get("group", {}).get("members", [])]

    # -- Group links --------------------------------------------------------

    async def create_group_link(
        self, group_id: int, role: str = "member"
    ) -> GroupLink:
        resp = await self.send_command(cmd.create_group_link(group_id, role))
        self._check_error(resp)
        return GroupLink.model_validate(resp.get("groupLink", resp))

    async def get_group_link(self, group_id: int) -> GroupLink:
        resp = await self.send_command(cmd.get_group_link(group_id))
        self._check_error(resp)
        return GroupLink.model_validate(resp.get("groupLink", resp))

    async def set_group_link_role(self, group_id: int, role: str) -> GroupLink:
        resp = await self.send_command(cmd.group_link_member_role(group_id, role))
        self._check_error(resp)
        return GroupLink.model_validate(resp.get("groupLink", resp))

    async def delete_group_link(self, group_id: int) -> None:
        resp = await self.send_command(cmd.delete_group_link(group_id))
        self._check_error(resp)

    # -- Files --------------------------------------------------------------

    async def receive_file(
        self,
        file_id: int,
        *,
        file_path: str | None = None,
        encrypt: bool | None = None,
        inline: bool | None = None,
    ) -> dict[str, Any]:
        resp = await self.send_command(
            cmd.receive_file(file_id, file_path=file_path, encrypt=encrypt, inline=inline)
        )
        self._check_error(resp)
        return resp

    async def cancel_file(self, file_id: int) -> dict[str, Any]:
        resp = await self.send_command(cmd.cancel_file(file_id))
        self._check_error(resp)
        return resp
