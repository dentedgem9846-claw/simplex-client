# simplex-client

Typed async Python client for the [SimpleX Chat CLI](https://github.com/simplex-chat/simplex-chat) WebSocket API.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

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
                print(f"Received: {item.chat_item.content.text}")

        # Run with auto-reconnect
        await client.run()

asyncio.run(main())
```

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
