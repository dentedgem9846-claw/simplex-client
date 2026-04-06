"""Minimal echo bot using simplex-client.

Usage:
    1. Start SimpleX Chat CLI: simplex-chat -p 5225
    2. Run this bot: python examples/echo_bot.py
    3. Connect to the bot's address from any SimpleX app
"""

import asyncio

from simplex_client import SimplexClient


async def main() -> None:
    async with SimplexClient("localhost", 5225) as client:
        user = await client.get_user()
        if user is None:
            user = await client.create_user("EchoBot")
            print(f"Created user: {user.profile.display_name}")

        # Create an address so people can connect
        try:
            address = await client.create_address(user.user_id)
            print(f"Bot address: {address.contact_link}")
        except Exception:
            address = await client.show_address(user.user_id)
            if address:
                print(f"Bot address: {address.contact_link}")

        # Echo back any received message
        @client.on_event("newChatItems")
        async def on_message(event):
            for item in event.chat_items:
                ci = item.chat_item
                if ci.content.type == "rcvMsgContent" and ci.content.text:
                    chat_info = item.chat_info
                    if chat_info.type == "direct" and chat_info.contact:
                        contact_id = chat_info.contact.contact_id
                        await client.send_message(
                            f"@{contact_id}",
                            [{"msgContent": {"type": "text", "text": ci.content.text}}],
                        )
                        print(f"Echoed: {ci.content.text}")

        @client.on_event("contactConnected")
        async def on_contact(event):
            print(f"New contact: {event.contact.profile.display_name}")

        print("Echo bot running… press Ctrl+C to stop")
        await client.run()


if __name__ == "__main__":
    asyncio.run(main())
