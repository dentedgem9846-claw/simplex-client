"""Unit tests for simplex_client.commands."""

import json

import pytest

from simplex_client import commands as cmd

pytestmark = pytest.mark.unit


class TestUserCommands:
    def test_show_active_user(self):
        assert cmd.show_active_user() == "/user"

    def test_create_active_user(self):
        profile = {"profile": {"displayName": "Bot"}, "pastTimestamp": False}
        result = cmd.create_active_user(profile)
        assert result.startswith("/_create user ")
        parsed = json.loads(result[len("/_create user "):])
        assert parsed["profile"]["displayName"] == "Bot"

    def test_list_users(self):
        assert cmd.list_users() == "/users"

    def test_set_active_user(self):
        assert cmd.set_active_user(42) == "/_user 42"

    def test_delete_user_smp_on(self):
        assert cmd.delete_user(1) == "/_delete user 1 del_smp=on"

    def test_delete_user_smp_off(self):
        assert cmd.delete_user(1, del_smp=False) == "/_delete user 1 del_smp=off"

    def test_update_profile(self):
        result = cmd.update_profile(1, {"displayName": "NewName"})
        assert result.startswith("/_profile 1 ")
        parsed = json.loads(result[len("/_profile 1 "):])
        assert parsed["displayName"] == "NewName"


class TestAddressCommands:
    def test_create_address(self):
        assert cmd.create_address(5) == "/_address 5"

    def test_delete_address(self):
        assert cmd.delete_address(5) == "/_delete_address 5"

    def test_show_address(self):
        assert cmd.show_address(5) == "/_show_address 5"

    def test_set_profile_address_on(self):
        assert cmd.set_profile_address(1, on=True) == "/_profile_address 1 on"

    def test_set_profile_address_off(self):
        assert cmd.set_profile_address(1, on=False) == "/_profile_address 1 off"

    def test_set_address_settings(self):
        result = cmd.set_address_settings(1, {"businessAddress": False})
        assert result.startswith("/_address_settings 1 ")


class TestConnectionCommands:
    def test_add_contact(self):
        assert cmd.add_contact(1) == "/_connect 1"

    def test_add_contact_incognito(self):
        assert cmd.add_contact(1, incognito=True) == "/_connect 1 incognito=on"

    def test_connect(self):
        assert cmd.connect_via_link(1, "https://link") == "/connect https://link"

    def test_connect_plan(self):
        assert cmd.connect_plan(1, "https://link") == "/_connect plan 1 https://link"

    def test_accept_contact(self):
        assert cmd.accept_contact(99) == "/_accept 99"

    def test_reject_contact(self):
        assert cmd.reject_contact(99) == "/_reject 99"


class TestContactCommands:
    def test_list_contacts(self):
        assert cmd.list_contacts(1) == "/_contacts 1"

    def test_list_groups(self):
        assert cmd.list_groups(1) == "/groups"

    def test_list_groups_with_search(self):
        assert cmd.list_groups(1, search="test") == "/_groups 1 test"

    def test_delete_chat(self):
        assert cmd.delete_chat("@5", "full") == "/_delete @5 full"


class TestMessageCommands:
    def test_send_messages(self):
        msgs = [{"msgContent": {"type": "text", "text": "hello"}}]
        result = cmd.send_messages("@5", msgs)
        assert result.startswith("/_send @5 json ")
        parsed = json.loads(result[len("/_send @5 json "):])
        assert parsed[0]["msgContent"]["text"] == "hello"

    def test_send_messages_with_live_and_ttl(self):
        msgs = [{"msgContent": {"type": "text", "text": "hi"}}]
        result = cmd.send_messages("@5", msgs, live=True, ttl=3600)
        assert " live=on" in result
        assert " ttl=3600" in result

    def test_update_chat_item(self):
        result = cmd.update_chat_item("@5", 100, {"msgContent": {"type": "text", "text": "edited"}})
        assert result.startswith("/_update item @5 100")

    def test_delete_chat_item(self):
        result = cmd.delete_chat_items("@5", [100, 101], "broadcast")
        assert result == "/_delete item @5 100,101 broadcast"

    def test_delete_member_chat_item(self):
        result = cmd.delete_member_chat_items(10, [200])
        assert result == "/_delete member item #10 200"

    def test_chat_item_reaction(self):
        result = cmd.chat_item_reaction("@5", 100, True, {"type": "emoji", "emoji": "👍"})
        assert "/_reaction @5 100 on" in result


class TestGroupCommands:
    def test_new_group(self):
        result = cmd.create_group(1, {"displayName": "Test", "fullName": ""})
        assert result.startswith("/_group 1 ")

    def test_create_group_incognito(self):
        result = cmd.create_group(1, {"displayName": "Test"}, incognito=True)
        assert " incognito=on" in result

    def test_update_group_profile(self):
        result = cmd.update_group_profile(10, {"displayName": "NewName"})
        assert result.startswith("/_group_profile #10 ")

    def test_add_member(self):
        assert cmd.add_member(10, 5, "admin") == "/_add #10 5 admin"

    def test_join_group(self):
        assert cmd.join_group(10) == "/_join #10"

    def test_accept_member(self):
        assert cmd.accept_member(10, 5, "member") == "/_accept member #10 5 member"

    def test_members_role(self):
        assert cmd.members_role(10, [1, 2], "admin") == "/_member role #10 1,2 admin"

    def test_block_members_for_all(self):
        assert cmd.block_members_for_all(10, [1]) == "/_block #10 1 blocked=on"

    def test_block_members_for_all_unblock(self):
        assert cmd.block_members_for_all(10, [1], blocked=False) == "/_block #10 1 blocked=off"

    def test_remove_members(self):
        assert cmd.remove_members(10, [1, 2]) == "/_remove #10 1,2"

    def test_remove_members_with_messages(self):
        assert cmd.remove_members(10, [1], with_messages=True) == "/_remove #10 1 messages=on"

    def test_leave_group(self):
        assert cmd.leave_group(10) == "/_leave #10"

    def test_list_members(self):
        assert cmd.list_members(10) == "/_members #10"


class TestGroupLinkCommands:
    def test_create_group_link(self):
        assert cmd.create_group_link(10, "member") == "/_create link #10 member"

    def test_group_link_member_role(self):
        assert cmd.group_link_member_role(10, "admin") == "/_set link role #10 admin"

    def test_delete_group_link(self):
        assert cmd.delete_group_link(10) == "/_delete link #10"

    def test_get_group_link(self):
        assert cmd.get_group_link(10) == "/_get link #10"


class TestFileCommands:
    def test_receive_file(self):
        assert cmd.receive_file(42) == "/freceive 42"

    def test_receive_file_with_options(self):
        result = cmd.receive_file(42, encrypt=True, inline=False, file_path="/tmp/out")
        assert "encrypt=on" in result
        assert "inline=off" in result
        assert "/tmp/out" in result

    def test_cancel_file(self):
        assert cmd.cancel_file(42) == "/fcancel 42"
