"""Turkish-specific Unicode casing helpers."""

_LOWER_TRANSLATION = str.maketrans({"I": "ı", "İ": "i"})
_UPPER_TRANSLATION = str.maketrans({"i": "İ", "ı": "I"})


def turkish_lower(text: str) -> str:
    """Lowercase text using the Turkish dotted/dotless I pairs."""
    return text.translate(_LOWER_TRANSLATION).lower()


def turkish_upper(text: str) -> str:
    """Uppercase text using the Turkish dotted/dotless I pairs."""
    return text.translate(_UPPER_TRANSLATION).upper()


def turkish_capitalize(text: str) -> str:
    """Capitalize the first character with Turkish casing rules."""
    if not text:
        return text
    return turkish_upper(text[0]) + turkish_lower(text[1:])
