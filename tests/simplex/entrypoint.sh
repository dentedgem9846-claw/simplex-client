#!/bin/bash
set -e

DISPLAY_NAME="${BOT_DISPLAY_NAME:-TestBot}"
DATA_PREFIX="/home/simplex/data/simplex"

# simplex-chat binds to 127.0.0.1 only, so we use socat to expose it on 0.0.0.0
# socat forwards 0.0.0.0:5225 -> 127.0.0.1:5226 (where simplex-chat listens)
socat TCP-LISTEN:5225,fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:5226 &

echo "Starting SimpleX Chat CLI WebSocket server on port 5226 (proxied to 5225)..."
exec simplex-chat -d "$DATA_PREFIX" -p 5226 --create-bot-display-name "$DISPLAY_NAME"
