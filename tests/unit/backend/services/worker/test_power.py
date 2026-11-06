"""The worker asks Windows not to throttle it (power.py, v1.0.1): the call and its arguments,
checked against a stand-in for Windows' kernel32."""

import ctypes
import sys
from typing import Any

from clearmd.backend.services.worker import power


class FakeKernel32:
    def __init__(self, *, answer: int = 1, missing: bool = False) -> None:
        self.calls: list[tuple[Any, ...]] = []
        self._answer = answer
        self._missing = missing

    def GetCurrentProcess(self) -> int:  # noqa: N802 -- Windows' own name
        return -1  # Windows' pseudo-handle for "this process"

    def SetProcessInformation(self, *args: Any) -> int:  # noqa: N802 -- Windows' own name
        if self._missing:
            raise AttributeError("SetProcessInformation")  # Windows before 8
        self.calls.append(args)
        state = ctypes.cast(args[2], ctypes.POINTER(power.ThrottlingState)).contents
        self.state = (state.Version, state.ControlMask, state.StateMask)
        return self._answer


def test_it_asks_for_full_execution_speed() -> None:
    kernel32 = FakeKernel32()
    assert power.keep_full_speed(kernel32)
    handle, information_class, _state, size = kernel32.calls[0]
    assert (handle, information_class) == (-1, 4)  # this process, ProcessPowerThrottling
    assert size == ctypes.sizeof(power.ThrottlingState) == 12
    # Version 1; the execution speed is controlled, and its state is "not throttled".
    assert kernel32.state == (1, 0x1, 0)


def test_a_refusal_or_an_older_windows_changes_nothing() -> None:
    assert not power.keep_full_speed(FakeKernel32(answer=0))
    assert not power.keep_full_speed(FakeKernel32(missing=True))


def test_the_real_call_succeeds_on_windows_and_does_nothing_elsewhere() -> None:
    # On Windows CI this is the real call: Windows must accept it (the handle's type matters).
    assert power.keep_full_speed() is (sys.platform == "win32")
