"""The Windows version resource of ClearMD's executables (feature 006b, ADR-0037): the product
name and version that SignPath checks before it signs. Plain text, read by PyInstaller."""

PRODUCT = "ClearMD"
DESCRIPTIONS = {
    "ClearMD.exe": "ClearMD: documents to Markdown (desktop app)",
    "clearmd-cli.exe": "ClearMD: documents to Markdown (command line)",
    "ClearMD-Qt.exe": "ClearMD: documents to Markdown (desktop app, Qt)",
}


def version_text(version: str, filename: str) -> str:
    """The version resource of one executable, for ``version``, in PyInstaller's text form."""
    numbers = [int(part) for part in version.split(".")[:3]]
    numbers += [0] * (4 - len(numbers))
    tuple_text = ", ".join(str(n) for n in numbers)
    strings = {
        "CompanyName": PRODUCT,
        "FileDescription": DESCRIPTIONS[filename],
        "FileVersion": version,
        "InternalName": filename.removesuffix(".exe"),
        "LegalCopyright": "MIT License, (c) 2026 Nicolas Enrique Valencia Santiago",
        "OriginalFilename": filename,
        "ProductName": PRODUCT,
        "ProductVersion": version,
    }
    pairs = (f"StringStruct({key!r}, {value!r})" for key, value in strings.items())
    table = ",\n          ".join(pairs)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple_text}),
    prodvers=({tuple_text}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [{table}])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
