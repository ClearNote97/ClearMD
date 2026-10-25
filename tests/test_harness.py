"""The test harness itself: the network guard is active in every test."""

import socket

import pytest
from support import NetworkBlockedError


def test_socket_connect_is_blocked() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        with pytest.raises(NetworkBlockedError):
            sock.connect(("127.0.0.1", 9))


def test_create_connection_is_blocked() -> None:
    with pytest.raises(NetworkBlockedError):
        socket.create_connection(("example.com", 443))
