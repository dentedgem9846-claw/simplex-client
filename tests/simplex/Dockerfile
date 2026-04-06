FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Download simplex-chat binary
RUN curl -L -o /usr/local/bin/simplex-chat \
    https://github.com/simplex-chat/simplex-chat/releases/latest/download/simplex-chat-ubuntu-22_04-x86-64 \
    && chmod +x /usr/local/bin/simplex-chat

RUN useradd -m simplex
USER simplex
WORKDIR /home/simplex

# Create data directory
RUN mkdir -p /home/simplex/data

EXPOSE 5225

# Default command runs WebSocket server
CMD ["simplex-chat", "-d", "/home/simplex/data", "-p", "5225"]
