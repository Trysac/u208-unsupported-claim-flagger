"""Flag answer sentences whose checkable facts do not appear in the context.

The package extracts dates, numbers, quotes, and names from each sentence of an
answer and verifies each fact literally against the supplied context. It is
deterministic, dependency-free, and does not require citations or an LLM judge.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "Claim",
    "Fact",
    "FlaggerError",
    "Report",
    "extract_facts",
    "flag",
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class FlaggerError(Exception):
    """Base error for unsupported_claim_flagger."""

    def __init__(
        self,
        code: Literal["input_too_large", "invalid_input"],
        message: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Fact:
    """A single checkable atom extracted from a sentence."""

    kind: Literal["date", "number", "quote", "name"]
    text: str
    normalized: str


@dataclass(frozen=True)
class Claim:
    """Result for a single sentence from the answer."""

    index: int
    sentence: str
    status: Literal["supported", "unsupported", "no_checkable_facts"]
    facts: tuple[Fact, ...]
    missing: tuple[str, ...]


@dataclass(frozen=True)
class Report:
    """Overall flagging report."""

    claims: tuple[Claim, ...]
    supported_ratio: float


# ---------------------------------------------------------------------------
# Date extraction
# ---------------------------------------------------------------------------

_MONTH_NAMES = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

_MONTH_ALT = "|".join(_MONTH_NAMES)

_DMY_RE = re.compile(rf"\b(\d{{1,2}})\s+({_MONTH_ALT})\s+(\d{{4}})\b")

_MDY_RE = re.compile(rf"\b({_MONTH_ALT})\s+(\d{{1,2}}),\s*(\d{{4}})\b")


def _parse_date(text: str, year: int, month: int, day: int) -> str | None:
    try:
        import datetime

        datetime.date(year, month, day)
        return f"{year:04d}-{month:02d}-{day:02d}"
    except ValueError:
        return None


def _extract_dates(sentence: str) -> list[tuple[int, int, str, str]]:
    """Return list of (start, end, text, normalized) of valid dates."""
    results: list[tuple[int, int, str, str]] = []

    for match in _ISO_DATE_RE.finditer(sentence):
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        normalized = _parse_date(match.group(0), year, month, day)
        if normalized:
            results.append((match.start(), match.end(), match.group(0), normalized))

    for match in _DMY_RE.finditer(sentence):
        day = int(match.group(1))
        month = _MONTH_NAMES[match.group(2)]
        year = int(match.group(3))
        normalized = _parse_date(match.group(0), year, month, day)
        if normalized:
            results.append((match.start(), match.end(), match.group(0), normalized))

    for match in _MDY_RE.finditer(sentence):
        month = _MONTH_NAMES[match.group(1)]
        day = int(match.group(2))
        year = int(match.group(3))
        normalized = _parse_date(match.group(0), year, month, day)
        if normalized:
            results.append((match.start(), match.end(), match.group(0), normalized))

    return results


# ---------------------------------------------------------------------------
# Quote extraction
# ---------------------------------------------------------------------------

_STRAIGHT_QUOTE_RE = re.compile(r'"([^"]*)"')
_CURLY_QUOTE_RE = re.compile(r"\u201c([^\u201d]*)\u201d")


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_quotes(sentence: str) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    for match in _STRAIGHT_QUOTE_RE.finditer(sentence):
        content = match.group(1)
        if 1 <= len(content) <= 300:
            normalized = _collapse_whitespace(content)
            results.append((match.start(), match.end(), content, normalized))
    for match in _CURLY_QUOTE_RE.finditer(sentence):
        content = match.group(1)
        if 1 <= len(content) <= 300:
            normalized = _collapse_whitespace(content)
            results.append((match.start(), match.end(), content, normalized))
    return results


# ---------------------------------------------------------------------------
# Number extraction
# ---------------------------------------------------------------------------

_NUMBER_RE = re.compile(r"(?<![\w.,-])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?")


def _normalize_number(text: str) -> str:
    """Normalize a number: drop group commas and trailing decimal zeros; keep '%'."""
    has_percent = text.endswith("%")
    if has_percent:
        text = text[:-1]
    # Remove commas (thousands separators)
    text = text.replace(",", "")
    if "." in text:
        integer_part, decimal_part = text.split(".", 1)
        # Strip trailing zeros from decimal part
        decimal_part = decimal_part.rstrip("0")
        text = f"{integer_part}.{decimal_part}" if decimal_part else integer_part
    if has_percent:
        text += "%"
    return text


def _extract_numbers(sentence: str) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    for match in _NUMBER_RE.finditer(sentence):
        text = match.group(0)
        normalized = _normalize_number(text)
        results.append((match.start(), match.end(), text, normalized))
    return results


# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"(?<![A-Za-z])([A-Z][a-z]+(?: [A-Z][a-z]+){0,3})(?![A-Za-z])")


def _is_first_word(sentence: str, match_start: int) -> bool:
    """Return True if there is no word (letter) before match_start in sentence."""
    return not any(char.isalpha() for char in sentence[:match_start])


def _extract_names(sentence: str) -> list[tuple[int, int, str, str]]:
    results: list[tuple[int, int, str, str]] = []
    for match in _NAME_RE.finditer(sentence):
        text = match.group(1)
        words = text.split()
        if len(words) == 1 and _is_first_word(sentence, match.start()):
            continue
        normalized = text
        results.append((match.start(), match.end(), text, normalized))
    return results


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------


def extract_facts(sentence: str) -> tuple[Fact, ...]:
    """Extract all checkable facts from a sentence in the defined priority order.

    The order is: dates, quotes, numbers, names. Each character span is consumed
    at most once; later fact types skip spans already taken by earlier types.
    """
    consumed: set[tuple[int, int]] = set()

    def _is_available(start: int, end: int) -> bool:
        return not any(
            start < consumed_end and consumed_start < end
            for consumed_start, consumed_end in consumed
        )

    selected: list[tuple[int, Fact]] = []

    def _add(
        kind: Literal["date", "number", "quote", "name"],
        spans: list[tuple[int, int, str, str]],
    ) -> None:
        for start, end, text, normalized in spans:
            if _is_available(start, end):
                selected.append((start, Fact(kind, text, normalized)))
                consumed.add((start, end))

    _add("date", _extract_dates(sentence))
    _add("quote", _extract_quotes(sentence))
    _add("number", _extract_numbers(sentence))
    _add("name", _extract_names(sentence))

    selected.sort(key=lambda item: item[0])
    return tuple(fact for _, fact in selected)


# ---------------------------------------------------------------------------
# Context processing
# ---------------------------------------------------------------------------


def _process_context(context: str | Sequence[str]) -> tuple[set[str], set[str], list[str]]:
    """Extract support data from context strings.

    Returns:
        date_set: set of normalized date strings from all contexts.
        number_set: set of normalized number strings from all contexts.
        collapsed_texts: list of whitespace-collapsed strings for each context.
    """
    context_list = [context] if isinstance(context, str) else list(context)

    date_set: set[str] = set()
    number_set: set[str] = set()
    collapsed_texts: list[str] = []

    for ctx in context_list:
        collapsed = _collapse_whitespace(ctx)
        collapsed_texts.append(collapsed)
        # Extract facts from the context string, but we only need dates and numbers.
        # We'll use extract_facts on each sentence? But the spec says context is
        # extracted the same way, per context string. So we split each context into
        # sentences and extract facts, then collect normalized dates and numbers.
        # However, for quotes and names, we use the whole collapsed text.
        sentences = _split_sentences(ctx)
        for sentence in sentences:
            facts = extract_facts(sentence)
            for fact in facts:
                if fact.kind == "date":
                    date_set.add(fact.normalized)
                elif fact.kind == "number":
                    number_set.add(fact.normalized)
    return date_set, number_set, collapsed_texts


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences after '.', '!', '?' followed by whitespace or end."""
    if not text.strip():
        return []
    # Add a trailing space to allow split at end without extra logic.
    parts = re.split(r"(?<=[.!?])\s+", text.strip() + " ")
    # Remove the last empty component if present
    return [p for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Flagging
# ---------------------------------------------------------------------------


def flag(
    answer: str,
    context: str | Sequence[str],
    *,
    max_chars: int = 200_000,
) -> Report:
    """Flag unsupported claims in *answer* against *context*.

    Args:
        answer: The text to check (typically an LLM answer).
        context: A string or sequence of strings containing the known facts.
        max_chars: Maximum total characters of answer plus all context strings.

    Returns:
        Report with claims for each sentence and the supported ratio.

    Raises:
        FlaggerError: If input exceeds size or sentence limits.
    """
    contexts = [context] if isinstance(context, str) else list(context)

    total_len = len(answer) + sum(len(c) for c in contexts)
    if total_len > max_chars:
        raise FlaggerError("input_too_large")

    sentences = _split_sentences(answer)
    if len(sentences) > 2000:
        raise FlaggerError("input_too_large")

    context_dates, context_numbers, collapsed_contexts = _process_context(contexts)

    claims: list[Claim] = []
    for idx, sentence in enumerate(sentences):
        facts = extract_facts(sentence)
        if not facts:
            claims.append(Claim(idx, sentence, "no_checkable_facts", facts, ()))
            continue

        missing: list[str] = []
        all_supported = True
        for fact in facts:
            supported = False
            if fact.kind == "date":
                supported = fact.normalized in context_dates
            elif fact.kind == "number":
                supported = fact.normalized in context_numbers
            elif fact.kind == "quote":
                supported = any(fact.normalized in collapsed for collapsed in collapsed_contexts)
            elif fact.kind == "name":
                pattern = re.compile(r"\b" + re.escape(fact.normalized) + r"\b")
                supported = any(pattern.search(collapsed) for collapsed in collapsed_contexts)
            if not supported:
                all_supported = False
                missing.append(fact.text)

        status: Literal["supported", "unsupported"]
        missing_tuple: tuple[str, ...]
        if all_supported:
            status = "supported"
            missing_tuple = ()
        else:
            status = "unsupported"
            missing_tuple = tuple(missing)
        claims.append(Claim(idx, sentence, status, facts, missing_tuple))

    supported_count = sum(1 for c in claims if c.status == "supported")
    unsupported_count = sum(1 for c in claims if c.status == "unsupported")
    denominator = supported_count + unsupported_count
    ratio = 1.0 if denominator == 0 else supported_count / denominator
    ratio = round(ratio, 6)

    return Report(tuple(claims), ratio)
