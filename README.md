# simplex-client

Typed async Python client for the [SimpleX Chat CLI](https://github.com/simplex-chat/simplex-chat) WebSocket API.

## Features

- Typed Pydantic models for all SimpleX Chat API types
- Async context manager with auto-reconnect
- `corrId`-based command/response correlation
- Event callback registration with `@client.on_event()`
- Full support for contacts, groups, messages, files, and group links

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.10+
- A running [SimpleX Chat CLI](https://github.com/simplex-chat/simplex-chat/blob/stable/docs/CLI.md) instance in WebSocket mode (`simplex-chat -p 5225`)

## Quick Start

```python
import asyncio
from simplex_client import SimplexClient

async def main():
    async with SimplexClient("localhost", 5225) as client:
        # Get or create user
        user = await client.get_user()
        if user is None:
            user = await client.create_user("MyBot")

        # Listen for messages
        @client.on_event("newChatItems")
        async def on_message(event):
            for item in event.chat_items:
                ci = item.chat_item
                if ci.content.type == "rcvMsgContent" and ci.content.text:
                    chat_info = item.chat_info
                    if chat_info.type == "direct":
                        print(f"Received: {ci.content.text}")

        # Run with auto-reconnect
        await client.run()

asyncio.run(main())
```

See [`examples/echo_bot.py`](examples/echo_bot.py) for a complete working bot.

## Running Tests

Unit tests only:

```bash
pytest -m "not integration"
```

Integration tests (requires Docker):

```bash
pytest -m integration
```

All tests:

```bash
pytest
```

## API Reference

See the [SimpleX Chat Bot API docs](https://github.com/simplex-chat/simplex-chat/tree/stable/bots) for the full protocol specification.

## License

AGPL-3.0-or-later
