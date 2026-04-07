FROM ubuntu:22.04

RUN apt-get update && apt-get install -y curl netcat-openbsd socat && rm -rf /var/lib/apt/lists/*

# Download simplex-chat binary (pinned version)
# NOTE: keep in sync with Chronocrystal/docker/simplex/Dockerfile
ARG SIMPLEX_VERSION=v6.4.11
RUN curl -L -o /usr/local/bin/simplex-chat \
    "https://github.com/simplex-chat/simplex-chat/releases/download/${SIMPLEX_VERSION}/simplex-chat-ubuntu-22_04-x86_64" \
    && chmod +x /usr/local/bin/simplex-chat

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN useradd -m simplex
USER simplex
WORKDIR /home/simplex

# Create data directory
RUN mkdir -p /home/simplex/data

EXPOSE 5225

ENTRYPOINT ["/entrypoint.sh"]
