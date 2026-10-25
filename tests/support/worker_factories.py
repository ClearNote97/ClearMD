"""Registry factories that the worker process imports by dotted path in the tests.

Each one first installs the network guard inside the worker (ADR-0005), then builds its registry.
``fake_registry`` behaves according to the source file's stem, to exercise every supervisor path.
"""

import os
import socket
import time
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import Detection, DetectionMethod
from clearmd.backend.services.conversion.registry import ConverterRegistry, build_registry
from support import install_network_guard

FAKE = "support.worker_factories:fake_registry"
REAL = "support.worker_factories:real_registry"


class FakeConverter:
    def convert(self, source: Path, detection: Detection) -> str:
        behavior = source.stem
        if behavior == "slow":
            time.sleep(60)
        elif behavior == "crash":
            os._exit(3)
        elif behavior == "hog":
            hoard = []
            for _ in range(60):  # up to ~1.2 GiB if the supervisor never stops it
                hoard.append(bytearray(20 * 1024**2))
                time.sleep(0.05)
        elif behavior == "corrupt":
            raise ConversionError(ErrorCode.CORRUPT_FILE, "BadZipFile: File is not a zip file")
        elif behavior == "boom":
            raise RuntimeError("unexpected failure")
        elif behavior == "network":
            socket.create_connection(("example.com", 443))
        elif behavior == "pid":
            return str(os.getpid())
        return f"# converted {source.name}"


class FakeContentDetector:
    """``detect_<format>`` names are detected as that format; ``crash`` kills the worker."""

    def detect(self, path: Path) -> Detection | None:
        if path.name == "crash":
            os._exit(3)
        prefix, _, value = path.name.partition("_")
        if prefix == "detect" and value in set(FormatId):
            return Detection(FormatId(value), DetectionMethod.CONTENT)
        return None


def fake_registry() -> ConverterRegistry:
    install_network_guard()
    return ConverterRegistry(
        dict.fromkeys(FormatId, FakeConverter()), content_detector=FakeContentDetector()
    )


def real_registry() -> ConverterRegistry:
    install_network_guard()
    return build_registry()
