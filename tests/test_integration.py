"""Integration tests requiring Docker containers.

Run with: pytest -m integration
"""

from __future__ import annotations

import asyncio

import pytest

from simplex_client import SimplexClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_two_bots_exchange_messages(simplex_bot1, simplex_bot2):
    """Test that two bots can connect and exchange messages.

    Flow:
    1. Connect client1 to bot1, client2 to bot2
    2. Create user profiles if not exist
    3. Bot1 creates a contact address
    4. Bot2 connects to bot1 using that address
    5. Wait for connection to establish
    6. Bot1 sends message to bot2
    7. Bot2 receives message
    8. Bot2 sends reply to bot1
    9. Bot1 receives reply
    """
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client1, \
               SimplexClient(simplex_bot2["host"], simplex_bot2["port"]) as client2:

        # Get or create users
        user1 = await client1.get_user()
        if user1 is None:
            user1 = await client1.create_user("TestBot1")

        user2 = await client2.get_user()
        if user2 is None:
            user2 = await client2.create_user("TestBot2")

        # Bot1 creates contact address
        address_response = await client1.create_address(user1.user_id)
        contact_link = address_response.contact_link

        # Set up message receivers
        received_by_bot1: asyncio.Queue = asyncio.Queue()
        received_by_bot2: asyncio.Queue = asyncio.Queue()

        @client1.on_event("newChatItems")
        async def bot1_receiver(event):
            for item in event.chat_items:
                if item.chat_item.content.type == "rcvMsgContent":
                    await received_by_bot1.put(item)

        @client2.on_event("newChatItems")
        async def bot2_receiver(event):
            for item in event.chat_items:
                if item.chat_item.content.type == "rcvMsgContent":
                    await received_by_bot2.put(item)

        # Bot2 connects to bot1 using address
        await client2.connect_contact(user2.user_id, contact_link)

        # Wait for connection (contactConnected event)
        await asyncio.sleep(5)

        # Get bot2's contact list to find bot1
        contacts = await client2.list_contacts(user2.user_id)
        assert len(contacts) >= 1
        bot1_contact = contacts[0]

        # Bot2 sends message to bot1
        test_message = "Hello from Bot2!"
        await client2.send_message(
            f"@{bot1_contact.contact_id}",
            [{"msgContent": {"type": "text", "text": test_message}}],
        )

        # Bot1 should receive the message
        received = await asyncio.wait_for(received_by_bot1.get(), timeout=10)
        assert received.chat_item.content.text == test_message

        # Bot1 sends reply
        reply_message = "Hello back from Bot1!"
        contacts1 = await client1.list_contacts(user1.user_id)
        bot2_contact = contacts1[0]

        await client1.send_message(
            f"@{bot2_contact.contact_id}",
            [{"msgContent": {"type": "text", "text": reply_message}}],
        )

        # Bot2 should receive the reply
        received_reply = await asyncio.wait_for(received_by_bot2.get(), timeout=10)
        assert received_reply.chat_item.content.text == reply_message


@pytest.mark.asyncio
async def test_client_reconnection(simplex_bot1):
    """Test that client reconnects after connection drop."""
    async with SimplexClient(simplex_bot1["host"], simplex_bot1["port"]) as client:
        user = await client.get_user()
        assert user is not None

        # Force disconnect
        await client._ws.close()

        # Wait for reconnection
        await asyncio.sleep(3)

        # Should be able to send commands again
        user_again = await client.get_user()
        assert user_again.user_id == user.user_id
