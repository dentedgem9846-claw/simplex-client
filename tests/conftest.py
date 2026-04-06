"""Pytest configuration and fixtures for simplex-client tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import websockets


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> Path:
    return pytestconfig.rootdir / "tests" / "docker-compose.yml"


def is_ws_responsive(host: str, port: int) -> bool:
    try:
        loop = asyncio.new_event_loop()

        async def check() -> bool:
            async with websockets.asyncio.client.connect(f"ws://{host}:{port}"):
                return True

        result = loop.run_until_complete(check())
        loop.close()
        return result
    except Exception:
        return False


@pytest.fixture(scope="session")
def simplex_bot1(docker_ip: str, docker_services: object) -> dict[str, str | int]:
    port = docker_services.port_for("simplex-bot1", 5225)  # type: ignore[attr-defined]
    docker_services.wait_until_responsive(  # type: ignore[attr-defined]
        timeout=60.0,
        pause=1.0,
        check=lambda: is_ws_responsive(docker_ip, port),
    )
    return {"host": docker_ip, "port": port}


@pytest.fixture(scope="session")
def simplex_bot2(docker_ip: str, docker_services: object) -> dict[str, str | int]:
    port = docker_services.port_for("simplex-bot2", 5225)  # type: ignore[attr-defined]
    docker_services.wait_until_responsive(  # type: ignore[attr-defined]
        timeout=60.0,
        pause=1.0,
        check=lambda: is_ws_responsive(docker_ip, port),
    )
    return {"host": docker_ip, "port": port}
