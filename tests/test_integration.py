"""Integration tests requiring Docker containers running SimpleX Chat CLI.

Run with: pytest -m integration

These tests require two SimpleX CLI instances running as WebSocket servers.
Use the provided docker-compose.yml to spin them up:

    docker compose -f tests/docker-compose.yml up -d --build
    pytest -m integration
    docker compose -f tests/docker-compose.yml down -v
"""

from __future__ import annotations

import asyncio

import pytest

from simplex_client import SimplexClient
from simplex_client.exceptions import SimplexError

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _wait_for_event(queue: asyncio.Queue, timeout: float = 15.0):
    """Wait for an item from a queue with a timeout."""
    return await asyncio.wait_for(queue.get(), timeout=timeout)


async def _ensure_user(client: SimplexClient, name: str):
    """Get existing user or create one."""
    user = await client.get_user()
    if user is None:
        user = await client.create_user(name)
    return user


async def _ensure_address(client: SimplexClient, user_id: int) -> str:
    """Get existing address or create one. Returns the contact link string."""
    addr = await client.show_address(user_id)
    if addr is None:
        addr = await client.create_address(user_id)
    return addr.contact_link


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect_and_get_user(simplex_bot1):
    """Basic connectivity: connect to CLI and retrieve/create a user."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        user = await _ensure_user(client, "IntegrationBot1")
        assert user.user_id > 0
        assert user.profile.display_name in ("IntegrationBot1", user.profile.display_name)


@pytest.mark.asyncio
async def test_create_and_show_address(simplex_bot1):
    """Create a contact address and verify it can be retrieved."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        user = await _ensure_user(client, "IntegrationBot1")

        # Delete existing address if any, then create fresh
        try:
            await client.delete_address(user.user_id)
        except SimplexError:
            pass

        addr = await client.create_address(user.user_id)
        assert addr.contact_link
        assert len(addr.contact_link) > 10

        # Verify we can retrieve it
        shown = await client.show_address(user.user_id)
        assert shown is not None
        assert shown.contact_link == addr.contact_link


@pytest.mark.asyncio
async def test_list_contacts_empty(simplex_bot2):
    """Listing contacts on a fresh instance returns a list (possibly empty)."""
    async with SimplexClient(simplex_bot2["host"], simplex_bot2["port"]) as client:
        user = await _ensure_user(client, "IntegrationBot2")
        contacts = await client.list_contacts(user.user_id)
        assert isinstance(contacts, list)


@pytest.mark.asyncio
async def test_list_groups_empty(simplex_bot1):
    """Listing groups returns a list."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        user = await _ensure_user(client, "IntegrationBot1")
        groups = await client.list_groups(user.user_id)
        assert isinstance(groups, list)


@pytest.mark.asyncio
async def test_two_bots_exchange_messages(simplex_bot1, simplex_bot2):
    """Full end-to-end: two bots connect and exchange messages.

    Flow:
    1. Connect client1 to bot1, client2 to bot2
    2. Create user profiles
    3. Bot1 creates a contact address
    4. Bot2 connects to bot1 using that address
    5. Wait for connection to establish
    6. Bot2 sends a message to bot1
    7. Bot1 receives the message
    8. Bot1 sends a reply
    9. Bot2 receives the reply
    """
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client1, \
               SimplexClient(simplex_bot2["host"], simplex_bot2["port"]) as client2:

        user1 = await _ensure_user(client1, "ExchangeBot1")
        user2 = await _ensure_user(client2, "ExchangeBot2")

        # Bot1 creates contact address
        contact_link = await _ensure_address(client1, user1.user_id)

        # Set up message receivers
        received_by_bot1: asyncio.Queue = asyncio.Queue()
        received_by_bot2: asyncio.Queue = asyncio.Queue()
        connected_to_bot1: asyncio.Queue = asyncio.Queue()

        @client1.on_event("newChatItems")
        async def bot1_msg(event):
            for item in event.chat_items:
                if item.chat_item.content.type == "rcvMsgContent":
                    await received_by_bot1.put(item)

        @client2.on_event("newChatItems")
        async def bot2_msg(event):
            for item in event.chat_items:
                if item.chat_item.content.type == "rcvMsgContent":
                    await received_by_bot2.put(item)

        @client1.on_event("contactConnected")
        async def bot1_contact(event):
            await connected_to_bot1.put(event)

        # Bot2 connects to bot1's address
        await client2.connect_contact(user2.user_id, contact_link)

        # Wait for bot1 to see the new contact
        contact_event = await _wait_for_event(connected_to_bot1, timeout=30.0)
        assert contact_event.contact.contact_id > 0

        # Give connection time to fully establish
        await asyncio.sleep(2)

        # Bot2 finds bot1 in contacts and sends a message
        contacts2 = await client2.list_contacts(user2.user_id)
        assert len(contacts2) >= 1
        bot1_contact = contacts2[0]

        test_message = "Hello from Bot2!"
        await client2.send_message(
            f"@{bot1_contact.contact_id}",
            [{"msgContent": {"type": "text", "text": test_message}}],
        )

        # Bot1 should receive it
        received = await _wait_for_event(received_by_bot1)
        assert received.chat_item.content.text == test_message

        # Bot1 replies
        contacts1 = await client1.list_contacts(user1.user_id)
        bot2_contact = next(
            c for c in contacts1 if c.contact_id == contact_event.contact.contact_id
        )

        reply_message = "Hello back from Bot1!"
        await client1.send_message(
            f"@{bot2_contact.contact_id}",
            [{"msgContent": {"type": "text", "text": reply_message}}],
        )

        # Bot2 should receive the reply
        reply = await _wait_for_event(received_by_bot2)
        assert reply.chat_item.content.text == reply_message


@pytest.mark.asyncio
async def test_send_and_receive_multiple_messages(simplex_bot1, simplex_bot2):
    """Send several messages in sequence and verify all are received in order."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client1, \
               SimplexClient(simplex_bot2["host"], simplex_bot2["port"]) as client2:

        user1 = await _ensure_user(client1, "MultiBot1")
        user2 = await _ensure_user(client2, "MultiBot2")

        # Ensure they're connected (reuse address from previous test or create)
        contact_link = await _ensure_address(client1, user1.user_id)

        connected: asyncio.Queue = asyncio.Queue()

        @client1.on_event("contactConnected")
        async def on_connect(event):
            await connected.put(event)

        # Check if already connected
        contacts2 = await client2.list_contacts(user2.user_id)
        if not contacts2:
            await client2.connect_contact(user2.user_id, contact_link)
            await _wait_for_event(connected, timeout=30.0)
            await asyncio.sleep(2)
            contacts2 = await client2.list_contacts(user2.user_id)

        bot1_contact = contacts2[0]

        received: asyncio.Queue = asyncio.Queue()

        @client1.on_event("newChatItems")
        async def on_msg(event):
            for item in event.chat_items:
                if item.chat_item.content.type == "rcvMsgContent":
                    await received.put(item.chat_item.content.text)

        # Send 5 messages
        messages = [f"Message {i}" for i in range(5)]
        for msg in messages:
            await client2.send_message(
                f"@{bot1_contact.contact_id}",
                [{"msgContent": {"type": "text", "text": msg}}],
            )

        # Receive all 5
        received_msgs = []
        for _ in range(5):
            text = await _wait_for_event(received, timeout=15.0)
            received_msgs.append(text)

        assert received_msgs == messages


@pytest.mark.asyncio
async def test_create_group(simplex_bot1):
    """Create a group and verify it appears in the group list."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        user = await _ensure_user(client, "GroupBot")

        group_info = await client.create_group(
            user.user_id,
            {"displayName": "TestGroup", "fullName": "Integration Test Group"},
        )
        assert group_info.group_id > 0
        assert group_info.group_profile.display_name == "TestGroup"

        # Verify it shows up in the list
        groups = await client.list_groups(user.user_id)
        group_ids = [g.get("groupInfo", {}).get("groupId") for g in groups if isinstance(g, dict)]
        assert group_info.group_id in group_ids


@pytest.mark.asyncio
async def test_event_handler_receives_contact_connected(simplex_bot1, simplex_bot2):
    """Verify the contactConnected event fires when a new contact connects."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client1, \
               SimplexClient(simplex_bot2["host"], simplex_bot2["port"]) as client2:

        user1 = await _ensure_user(client1, "EventBot1")
        user2 = await _ensure_user(client2, "EventBot2")

        # Delete and recreate address to get a fresh connection
        try:
            await client1.delete_address(user1.user_id)
        except SimplexError:
            pass
        addr = await client1.create_address(user1.user_id)

        events_received: asyncio.Queue = asyncio.Queue()

        @client1.on_event("contactConnected")
        async def handler(event):
            await events_received.put(event.type)

        await client2.connect_contact(user2.user_id, addr.contact_link)

        event_type = await _wait_for_event(events_received, timeout=30.0)
        assert event_type == "contactConnected"


@pytest.mark.asyncio
async def test_error_on_invalid_command(simplex_bot1):
    """Sending an invalid command should raise SimplexError."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        # Try to delete a non-existent address
        with pytest.raises(SimplexError):
            await client.delete_address(999999)
