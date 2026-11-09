"""Behaviour tests for the public API of unsupported_claim_flagger."""

from __future__ import annotations

import dataclasses

import pytest

import unsupported_claim_flagger
from unsupported_claim_flagger import (
    Claim,
    Fact,
    FlaggerError,
    Report,
    extract_facts,
    flag,
)


def test_public_api_exports() -> None:
    assert unsupported_claim_flagger.__all__ == [
        "Claim",
        "Fact",
        "FlaggerError",
        "Report",
        "extract_facts",
        "flag",
    ]


def test_dataclasses_are_frozen() -> None:
    fact = Fact("number", "1", "1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        fact.text = "2"
    claim = Claim(0, "sentence", "supported", (fact,), ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        claim.status = "unsupported"
    report = Report((claim,), 1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.supported_ratio = 0.5


def test_error_code_and_message_hides_texts() -> None:
    with pytest.raises(FlaggerError) as excinfo:
        flag("secret answer", "secret context", max_chars=5)
    assert excinfo.value.code == "input_too_large"
    assert "secret" not in str(excinfo.value)


def test_no_checkable_facts_ratio() -> None:
    report = flag("It went well.", "Some context.")
    assert report.supported_ratio == 1.0
    assert report.claims[0].status == "no_checkable_facts"
    assert report.claims[0].facts == ()


def test_extract_facts_returns_tuple() -> None:
    facts = extract_facts("The value is 42.")
    assert isinstance(facts, tuple)
    assert any(fact.kind == "number" and fact.normalized == "42" for fact in facts)
