from clearmd.backend.schemas.errors import ConversionError, ErrorCode, SkipReason


def test_conversion_error_carries_code_and_detail() -> None:
    error = ConversionError(ErrorCode.CORRUPT_FILE, "BadZipFile: File is not a zip file")
    assert error.code is ErrorCode.CORRUPT_FILE
    assert error.detail == "BadZipFile: File is not a zip file"
    assert "corrupt_file" in str(error)


def test_codes_are_stable_snake_case_identifiers() -> None:
    for value in [*ErrorCode, *SkipReason]:
        assert value.value == value.value.lower()
        assert " " not in value.value


def test_catalog_keys() -> None:
    assert ErrorCode.PASSWORD_PROTECTED.message_key == "error.password_protected.message"
    assert ErrorCode.PASSWORD_PROTECTED.action_key == "error.password_protected.action"
    assert SkipReason.TOO_LARGE.key == "skip.too_large"
