import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("debug", True),
        ("release", False),
        ("dev", True),
        ("prod", False),
        (1, True),
        (0, False),
    ],
)
def test_settings_debug_parser_valid_values(raw, expected) -> None:
    settings = Settings(debug=raw)

    assert settings.debug is expected


def test_settings_debug_parser_invalid_value() -> None:
    with pytest.raises(ValidationError):
        Settings(debug="unexpected-value")
