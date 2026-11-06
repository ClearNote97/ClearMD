"""The worker runs at full speed on Windows (v1.0.1).

Windows 11 slows down the processes it takes for background work (Efficiency mode, "EcoQoS":
efficiency cores, a lower clock). It decides by the window: with the flet app, the window belongs
to flet's own program, so ClearMD's processes may look like background ones, and a PDF took four
times as long on the owner's computer as with the other apps. A program may tell Windows not to
throttle it (``SetProcessInformation`` with ``ProcessPowerThrottling``); the worker does, at start.
Elsewhere this does nothing.
"""

import ctypes
import sys
from typing import Any

PROCESS_POWER_THROTTLING = 4  # PROCESS_INFORMATION_CLASS: ProcessPowerThrottling
THROTTLING_VERSION = 1  # PROCESS_POWER_THROTTLING_CURRENT_VERSION
EXECUTION_SPEED = 0x1  # PROCESS_POWER_THROTTLING_EXECUTION_SPEED


class ThrottlingState(ctypes.Structure):
    """PROCESS_POWER_THROTTLING_STATE (three ULONGs, 32 bits on Windows): control the
    speed, and set it to "not throttled"."""

    _fields_ = (
        ("Version", ctypes.c_uint32),
        ("ControlMask", ctypes.c_uint32),
        ("StateMask", ctypes.c_uint32),
    )


def keep_full_speed(kernel32: Any = None) -> bool:
    """Ask Windows not to throttle this process; True when it agreed. Never raises: a Windows
    without the call (before 10) keeps the old behaviour."""
    if kernel32 is None:
        if sys.platform != "win32":
            return False
        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined,unused-ignore]
    state = ThrottlingState(THROTTLING_VERSION, EXECUTION_SPEED, 0)
    try:
        done = kernel32.SetProcessInformation(
            kernel32.GetCurrentProcess(),
            PROCESS_POWER_THROTTLING,
            ctypes.byref(state),
            ctypes.sizeof(state),
        )
    except (AttributeError, OSError):
        return False
    return bool(done)
