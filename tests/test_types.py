"""Unit tests for simplex_client.types."""

import pytest

from simplex_client.types import (
    AChatItem,
    ChatInfo,
    ChatItem,
    ChatRef,
    ChatType,
    CIContent,
    CIMeta,
    ComposedMessage,
    Contact,
    ContactStatus,
    CreatedConnLink,
    GroupInfo,
    GroupMember,
    GroupMemberRole,
    GroupMemberStatus,
    LocalProfile,
    MsgContentFile,
    MsgContentImage,
    MsgContentText,
    MsgContentUnknown,
    Profile,
    User,
    UserContactLink,
)

pytestmark = pytest.mark.unit


class TestProfile:
    def test_parse_minimal(self):
        p = Profile.model_validate({"displayName": "Alice"})
        assert p.display_name == "Alice"
        assert p.full_name == ""
        assert p.image is None

    def test_parse_full(self):
        p = Profile.model_validate(
            {"displayName": "Alice", "fullName": "Alice Smith", "image": "base64data"}
        )
        assert p.full_name == "Alice Smith"
        assert p.image == "base64data"

    def test_extra_fields_ignored(self):
        p = Profile.model_validate(
            {"displayName": "Bob", "unknownField": True, "anotherOne": [1, 2]}
        )
        assert p.display_name == "Bob"


class TestLocalProfile:
    def test_parse(self):
        lp = LocalProfile.model_validate(
            {"profileId": 1, "displayName": "Bot", "fullName": "", "localAlias": ""}
        )
        assert lp.profile_id == 1
        assert lp.display_name == "Bot"


class TestUser:
    USER_JSON = {
        "userId": 1,
        "agentUserId": 100,
        "userContactId": 200,
        "localDisplayName": "testbot",
        "profile": {
            "profileId": 10,
            "displayName": "TestBot",
            "fullName": "",
            "localAlias": "",
        },
        "activeUser": True,
        "activeOrder": 1,
        "showNtfs": True,
        "sendRcptsContacts": False,
        "sendRcptsSmallGroups": False,
    }

    def test_parse(self):
        u = User.model_validate(self.USER_JSON)
        assert u.user_id == 1
        assert u.local_display_name == "testbot"
        assert u.profile.display_name == "TestBot"
        assert u.active_user is True

    def test_extra_fields_ignored(self):
        data = {**self.USER_JSON, "extraField": "ignore_me"}
        u = User.model_validate(data)
        assert u.user_id == 1


class TestContact:
    def test_parse_minimal(self):
        c = Contact.model_validate(
            {
                "contactId": 42,
                "localDisplayName": "alice",
                "profile": {
                    "profileId": 5,
                    "displayName": "Alice",
                    "fullName": "",
                    "localAlias": "",
                },
                "chatSettings": {"enableNtfs": "all"},
                "contactGrpInvSent": False,
                "chatDeleted": False,
            }
        )
        assert c.contact_id == 42
        assert c.local_display_name == "alice"
        assert c.contact_status == ContactStatus.active


class TestCreatedConnLink:
    def test_str_prefers_short(self):
        link = CreatedConnLink.model_validate(
            {"connFullLink": "https://full.link", "connShortLink": "https://short.link"}
        )
        assert str(link) == "https://short.link"

    def test_str_falls_back_to_full(self):
        link = CreatedConnLink.model_validate({"connFullLink": "https://full.link"})
        assert str(link) == "https://full.link"


class TestChatRef:
    def test_direct(self):
        cr = ChatRef.model_validate({"chatType": "direct", "chatId": 5})
        assert str(cr) == "@5"

    def test_group(self):
        cr = ChatRef.model_validate({"chatType": "group", "chatId": 10})
        assert str(cr) == "#10"

    def test_local(self):
        cr = ChatRef.model_validate({"chatType": "local", "chatId": 1})
        assert str(cr) == "*1"


class TestMsgContent:
    def test_text(self):
        from pydantic import TypeAdapter
        from simplex_client.types import MsgContent

        ta = TypeAdapter(MsgContent)
        mc = ta.validate_python({"type": "text", "text": "hello"})
        assert isinstance(mc, MsgContentText)
        assert mc.text == "hello"

    def test_image(self):
        from pydantic import TypeAdapter
        from simplex_client.types import MsgContent

        ta = TypeAdapter(MsgContent)
        mc = ta.validate_python({"type": "image", "text": "pic", "image": "base64"})
        assert isinstance(mc, MsgContentImage)
        assert mc.image == "base64"

    def test_file(self):
        from pydantic import TypeAdapter
        from simplex_client.types import MsgContent

        ta = TypeAdapter(MsgContent)
        mc = ta.validate_python({"type": "file", "text": "doc.pdf"})
        assert isinstance(mc, MsgContentFile)

    def test_unknown_type_falls_back(self):
        from pydantic import TypeAdapter
        from simplex_client.types import MsgContent

        ta = TypeAdapter(MsgContent)
        mc = ta.validate_python({"type": "futureType", "text": "something"})
        assert isinstance(mc, MsgContentUnknown)


class TestGroupMember:
    def test_parse(self):
        gm = GroupMember.model_validate(
            {
                "groupMemberId": 1,
                "groupId": 2,
                "memberId": "abc",
                "memberRole": "admin",
                "memberCategory": "user",
                "memberStatus": "connected",
                "blockedByAdmin": False,
                "localDisplayName": "alice",
                "memberProfile": {
                    "profileId": 10,
                    "displayName": "Alice",
                    "fullName": "",
                    "localAlias": "",
                },
                "memberContactProfileId": 10,
            }
        )
        assert gm.member_role == GroupMemberRole.admin
        assert gm.member_status == GroupMemberStatus.connected


class TestChatItem:
    CHAT_ITEM_JSON = {
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
    }

    def test_parse(self):
        ci = ChatItem.model_validate(self.CHAT_ITEM_JSON)
        assert ci.meta.item_id == 100
        assert ci.content.text == "Hello!"
        assert ci.content.type == "rcvMsgContent"

    def test_achat_item(self):
        aci = AChatItem.model_validate(
            {
                "chatInfo": {"type": "direct", "contact": {
                    "contactId": 1,
                    "localDisplayName": "bob",
                    "profile": {"profileId": 1, "displayName": "Bob", "fullName": "", "localAlias": ""},
                    "chatSettings": {},
                    "contactGrpInvSent": False,
                    "chatDeleted": False,
                }},
                "chatItem": self.CHAT_ITEM_JSON,
            }
        )
        assert aci.chat_info.type == "direct"
        assert aci.chat_item.meta.item_text == "Hello!"


class TestUserContactLink:
    def test_contact_link_property(self):
        ucl = UserContactLink.model_validate(
            {
                "userContactLinkId": 1,
                "connLinkContact": {
                    "connFullLink": "https://simplex.chat/full",
                    "connShortLink": "https://simplex.chat/short",
                },
                "shortLinkDataSet": False,
                "shortLinkLargeDataSet": False,
                "addressSettings": {
                    "businessAddress": False,
                },
            }
        )
        assert ucl.contact_link == "https://simplex.chat/full"


class TestComposedMessage:
    def test_parse(self):
        cm = ComposedMessage.model_validate(
            {"msgContent": {"type": "text", "text": "hi"}, "mentions": {}}
        )
        assert cm.msg_content["type"] == "text"
