from __future__ import annotations

import re

SENTENCE_TERMINATORS = frozenset(".!?…。｡．！？")
SENTENCE_CLOSERS = frozenset("\"'”’»」』】〉》〕〗〙〛)]}")


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("transcript tidak memuat satu kalimat pun")

    sentences: list[str] = []
    start = 0
    index = 0
    while index < len(normalized):
        character = normalized[index]
        if character not in SENTENCE_TERMINATORS or _is_decimal_point(normalized, index):
            index += 1
            continue

        index += 1
        while index < len(normalized) and normalized[index] in SENTENCE_TERMINATORS:
            index += 1
        while index < len(normalized) and normalized[index] in SENTENCE_CLOSERS:
            index += 1
        sentence = normalized[start:index].strip()
        if sentence:
            sentences.append(sentence)
        start = index

    remainder = normalized[start:].strip()
    if remainder:
        sentences.append(remainder)
    if not sentences:
        raise ValueError("transcript tidak memuat satu kalimat pun")
    return sentences


def _is_decimal_point(text: str, index: int) -> bool:
    return (
        text[index] == "."
        and index > 0
        and index + 1 < len(text)
        and text[index - 1].isdigit()
        and text[index + 1].isdigit()
    )
