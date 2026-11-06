"""The tests' network guard (ADR-0005) lets an in-process pipe through and nothing else: asyncio's
event loop needs one, and on Windows Python builds it over 127.0.0.1 (flet's tests, feature 018)."""

import socket

import pytest
import support


def test_a_local_pipe_works_and_the_guard_is_back_afterwards() -> None:
    left, right = support.local_pair()
    try:
        left.sendall(b"ok")
        assert right.recv(2) == b"ok"
    finally:
        left.close()
        right.close()
    assert socket.socket.connect is support.blocked


def test_any_other_connection_is_still_refused() -> None:
    with pytest.raises(support.NetworkBlockedError):
        socket.create_connection(("127.0.0.1", 9))
    probe = socket.socket()
    try:
        with pytest.raises(support.NetworkBlockedError):
            probe.connect(("127.0.0.1", 9))
    finally:
        probe.close()
