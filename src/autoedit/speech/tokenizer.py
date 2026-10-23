from __future__ import annotations

import unicodedata


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens: list[str] = []
    buffered: list[str] = []
    for character in normalized:
        if _is_cjk_or_hangul(character):
            if buffered:
                tokens.append("".join(buffered))
                buffered.clear()
            tokens.append(character)
        elif character.isalnum() or unicodedata.category(character).startswith("M"):
            buffered.append(character)
        elif buffered:
            tokens.append("".join(buffered))
            buffered.clear()
    if buffered:
        tokens.append("".join(buffered))
    return tokens


def _is_cjk_or_hangul(character: str) -> bool:
    codepoint = ord(character)
    return any(
        start <= codepoint <= end
        for start, end in (
            (0x3040, 0x30FF),
            (0x31F0, 0x31FF),
            (0x3400, 0x4DBF),
            (0x4E00, 0x9FFF),
            (0xF900, 0xFAFF),
            (0x1100, 0x11FF),
            (0x3130, 0x318F),
            (0xAC00, 0xD7AF),
        )
    )
