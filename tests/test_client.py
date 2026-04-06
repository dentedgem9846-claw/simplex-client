"""Unit tests for simplex_client.client (with mocked WebSocket)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from simplex_client.client import SimplexClient
from simplex_client.exceptions import SimplexConnectionError, SimplexError

pytestmark = pytest.mark.unit

# -- Fixtures ----------------------------------------------------------------

USER_RESP = {
    "type": "activeUser",
    "user": {
        "userId": 1,
        "agentUserId": 100,
        "userContactId": 200,
        "localDisplayName": "bot",
        "profile": {"profileId": 10, "displayName": "Bot", "fullName": "", "localAlias": ""},
        "activeUser": True,
        "activeOrder": 1,
    },
}

NO_USER_RESP = {
    "type": "chatCmdError",
    "chatError": {
        "type": "error",
        "errorType": {"type": "noActiveUser"},
    },
}

CONTACTS_RESP = {
    "type": "contactsList",
    "contacts": [
        {
            "contactId": 5,
            "localDisplayName": "alice",
            "profile": {"profileId": 20, "displayName": "Alice", "fullName": "", "localAlias": ""},
            "chatSettings": {},
            "contactGrpInvSent": False,
            "chatDeleted": False,
        }
    ],
}


class MockWebSocket:
    """Simulate a websockets connection for unit testing."""

    def __init__(self, responses: list[dict] | None = None) -> None:
        self._responses = responses or []
        self._response_idx = 0
        self._sent: list[str] = []
        self._closed = False
        self._recv_queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, data: str) -> None:
        self._sent.append(data)
        # Parse the command to get the corrId, then enqueue response
        parsed = json.loads(data)
        corr_id = parsed.get("corrId")
        if self._response_idx < len(self._responses):
            resp = self._responses[self._response_idx]
            self._response_idx += 1
            msg = json.dumps({"corrId": corr_id, "resp": resp})
            await self._recv_queue.put(msg)

    async def recv(self) -> str:
        return await self._recv_queue.get()

    async def close(self) -> None:
        self._closed = True
        # Unblock any waiting recv
        await self._recv_queue.put("")

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        if self._closed:
            raise StopAsyncIteration
        msg = await self._recv_queue.get()
        if not msg:
            raise StopAsyncIteration
        return msg


# -- Tests -------------------------------------------------------------------


class TestSendCommand:
    @pytest.mark.asyncio
    async def test_send_and_receive(self):
        mock_ws = MockWebSocket([USER_RESP])
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        resp = await client.send_command("/user")
        assert resp["type"] == "activeUser"
        assert resp["user"]["userId"] == 1

        client._closed = True
        await mock_ws.close()

    @pytest.mark.asyncio
    async def test_send_not_connected_raises(self):
        client = SimplexClient()
        with pytest.raises(SimplexConnectionError, match="not connected"):
            await client.send_command("/user")


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_user_exists(self):
        mock_ws = MockWebSocket([USER_RESP])
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        user = await client.get_user()
        assert user is not None
        assert user.user_id == 1
        assert user.profile.display_name == "Bot"

        client._closed = True
        await mock_ws.close()

    @pytest.mark.asyncio
    async def test_get_user_none(self):
        mock_ws = MockWebSocket([NO_USER_RESP])
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        user = await client.get_user()
        assert user is None

        client._closed = True
        await mock_ws.close()


class TestListContacts:
    @pytest.mark.asyncio
    async def test_list_contacts(self):
        mock_ws = MockWebSocket([CONTACTS_RESP])
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        contacts = await client.list_contacts(1)
        assert len(contacts) == 1
        assert contacts[0].contact_id == 5
        assert contacts[0].local_display_name == "alice"

        client._closed = True
        await mock_ws.close()


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_command_error_raises(self):
        error_resp = {
            "type": "chatCmdError",
            "chatError": {
                "type": "error",
                "errorType": {"type": "invalidConnReq"},
            },
        }
        mock_ws = MockWebSocket([error_resp])
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        with pytest.raises(SimplexError):
            await client.list_contacts(1)

        client._closed = True
        await mock_ws.close()


class TestEventDispatch:
    @pytest.mark.asyncio
    async def test_event_handler_called(self):
        client = SimplexClient()
        received = []

        @client.on_event("contactConnected")
        async def handler(event):
            received.append(event)

        mock_ws = MockWebSocket()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        # Inject an unsolicited event (no corrId)
        event_data = {
            "resp": {
                "type": "contactConnected",
                "user": USER_RESP["user"],
                "contact": CONTACTS_RESP["contacts"][0],
            }
        }
        await mock_ws._recv_queue.put(json.dumps(event_data))

        # Give the listener time to process
        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0].type == "contactConnected"

        client._closed = True
        await mock_ws.close()


class TestCorrIdCorrelation:
    @pytest.mark.asyncio
    async def test_multiple_commands_correlate(self):
        """Two commands sent concurrently get the right responses."""
        mock_ws = MockWebSocket()
        client = SimplexClient()
        client._ws = mock_ws  # type: ignore[assignment]
        client._listener_task = asyncio.create_task(client._listen())

        # Send two commands concurrently
        task1 = asyncio.create_task(client.send_command("/user"))
        task2 = asyncio.create_task(client.send_command("/users"))

        # Wait for both sends
        await asyncio.sleep(0.05)

        # Respond out of order (task2 first, then task1)
        await mock_ws._recv_queue.put(
            json.dumps({"corrId": "2", "resp": {"type": "usersList", "users": []}})
        )
        await mock_ws._recv_queue.put(
            json.dumps({"corrId": "1", "resp": USER_RESP})
        )

        resp1 = await task1
        resp2 = await task2

        assert resp1["type"] == "activeUser"
        assert resp2["type"] == "usersList"

        client._closed = True
        await mock_ws.close()
