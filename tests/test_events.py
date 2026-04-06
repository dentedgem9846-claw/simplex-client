"""Unit tests for simplex_client.events."""

import pytest

from simplex_client.events import (
    ChatErrorEvent,
    ContactConnectedEvent,
    Event,
    NewChatItemsEvent,
    ReceivedGroupInvitationEvent,
    RcvFileCompleteEvent,
    parse_event,
)

pytestmark = pytest.mark.unit

# Reusable user fixture
USER = {
    "userId": 1,
    "agentUserId": 100,
    "userContactId": 200,
    "localDisplayName": "bot",
    "profile": {"profileId": 10, "displayName": "Bot", "fullName": "", "localAlias": ""},
    "activeUser": True,
    "activeOrder": 1,
}

CONTACT = {
    "contactId": 5,
    "localDisplayName": "alice",
    "profile": {"profileId": 20, "displayName": "Alice", "fullName": "", "localAlias": ""},
    "chatSettings": {},
    "contactGrpInvSent": False,
    "chatDeleted": False,
}


class TestParseEvent:
    def test_contact_connected(self):
        event = parse_event({
            "type": "contactConnected",
            "user": USER,
            "contact": CONTACT,
        })
        assert isinstance(event, ContactConnectedEvent)
        assert event.user.user_id == 1
        assert event.contact.contact_id == 5

    def test_new_chat_items(self):
        event = parse_event({
            "type": "newChatItems",
            "user": USER,
            "chatItems": [
                {
                    "chatInfo": {"type": "direct", "contact": CONTACT},
                    "chatItem": {
                        "chatDir": {"type": "directRcv"},
                        "meta": {
                            "itemId": 100,
                            "itemTs": "2024-01-01T00:00:00Z",
                            "itemText": "Hello!",
                            "itemStatus": {"type": "rcvNew"},
                            "itemEdited": False,
                            "deletable": True,
                            "editable": False,
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-01T00:00:00Z",
                        },
                        "content": {"type": "rcvMsgContent", "text": "Hello!"},
                        "reactions": [],
                    },
                }
            ],
        })
        assert isinstance(event, NewChatItemsEvent)
        assert len(event.chat_items) == 1
        assert event.chat_items[0].chat_item.content.text == "Hello!"

    def test_unknown_event_returns_generic(self):
        event = parse_event({"type": "someNewFutureEvent", "data": 123})
        assert isinstance(event, Event)
        assert not isinstance(event, ContactConnectedEvent)
        assert event.type == "someNewFutureEvent"

    def test_chat_error_event(self):
        event = parse_event({
            "type": "chatError",
            "chatError": {
                "type": "error",
                "errorType": {"type": "noActiveUser"},
            },
        })
        assert isinstance(event, ChatErrorEvent)
        assert event.chat_error.type == "error"

    def test_extra_fields_ignored(self):
        event = parse_event({
            "type": "contactConnected",
            "user": USER,
            "contact": CONTACT,
            "totallyNewField": {"nested": True},
        })
        assert isinstance(event, ContactConnectedEvent)

    def test_received_group_invitation(self):
        group_member = {
            "groupMemberId": 1,
            "groupId": 2,
            "memberId": "abc",
            "memberRole": "member",
            "memberCategory": "user",
            "memberStatus": "connected",
            "blockedByAdmin": False,
            "localDisplayName": "bot",
            "memberProfile": {"profileId": 10, "displayName": "Bot", "fullName": "", "localAlias": ""},
            "memberContactProfileId": 10,
        }
        event = parse_event({
            "type": "receivedGroupInvitation",
            "user": USER,
            "groupInfo": {
                "groupId": 2,
                "localDisplayName": "testgroup",
                "groupProfile": {"displayName": "TestGroup", "fullName": ""},
                "membership": group_member,
                "chatSettings": {},
            },
            "contact": CONTACT,
            "memberRole": "member",
        })
        assert isinstance(event, ReceivedGroupInvitationEvent)
        assert event.group_info.group_id == 2

    def test_rcv_file_complete(self):
        event = parse_event({
            "type": "rcvFileComplete",
            "user": USER,
            "chatItem": {
                "chatInfo": {"type": "direct", "contact": CONTACT},
                "chatItem": {
                    "chatDir": {"type": "directRcv"},
                    "meta": {
                        "itemId": 50,
                        "itemTs": "2024-01-01T00:00:00Z",
                        "itemText": "",
                        "itemStatus": {"type": "rcvRead"},
                        "itemEdited": False,
                        "deletable": False,
                        "editable": False,
                        "createdAt": "2024-01-01T00:00:00Z",
                        "updatedAt": "2024-01-01T00:00:00Z",
                    },
                    "content": {"type": "rcvMsgContent", "text": ""},
                    "reactions": [],
                },
            },
        })
        assert isinstance(event, RcvFileCompleteEvent)
