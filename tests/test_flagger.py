"""Tests for unsupported_claim_flagger."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from unsupported_claim_flagger import (
    FlaggerError,
    extract_facts,
    flag,
)
from unsupported_claim_flagger.__main__ import main

# ---------------------------------------------------------------------------
# Acceptance tests (verbatim from specification)
# ---------------------------------------------------------------------------


def test_acceptance_supported_number_percent():
    report = flag("Revenue grew 12% to $1,200 in 2024.", "In 2024 revenue reached $1200, up 12%.")
    assert len(report.claims) == 1
    claim = report.claims[0]
    assert claim.status == "supported"
    assert claim.missing == ()


def test_acceptance_unsupported_percent():
    report = flag("Revenue grew 15% in 2024.", "In 2024 revenue reached $1200, up 12%.")
    assert len(report.claims) == 1
    claim = report.claims[0]
    assert claim.status == "unsupported"
    assert claim.missing == ("15%",)


def test_acceptance_extract_facts_numbers():
    facts = extract_facts("It costs 3.50 for 5km in COVID-19 times.")
    number_facts = [f for f in facts if f.kind == "number"]
    # 3.50 normalizes to 3.5, 5 normalizes to 5, 1,000,000 to 1000000, 10.0 to 10
    # In this sentence we also get "3.50", "5" (unit km allowed), "19" inside COVID-19 not matched
    texts = [f.text for f in number_facts]
    normalized = [f.normalized for f in number_facts]
    assert "3.50" in texts
    assert "5" in texts
    assert "19" not in texts
    idx_350 = texts.index("3.50")
    assert normalized[idx_350] == "3.5"
    idx_5 = texts.index("5")
    assert normalized[idx_5] == "5"


def test_acceptance_extract_facts_commas_and_decimals():
    facts = extract_facts("It costs 1,000,000 and 10.0.")
    number_facts = [f for f in facts if f.kind == "number"]
    # Should have two numbers
    assert len(number_facts) == 2
    texts = [f.text for f in number_facts]
    normalized = [f.normalized for f in number_facts]
    assert "1,000,000" in texts
    assert "10.0" in texts
    assert "1000000" in normalized
    assert "10" in normalized


def test_acceptance_dates_supported_both_formats():
    # ISO to D Month YYYY
    report1 = flag("The release was on 2026-11-09.", "Released 9 November 2026.")
    assert report1.claims[0].status == "supported"
    # ISO to Month D, YYYY
    report2 = flag("The release was on 2026-11-09.", "Released November 9, 2026.")
    assert report2.claims[0].status == "supported"


def test_acceptance_quotes_supported_and_unsupported():
    # Supported: whitespace collapsed
    report_sup = flag('She said "growth is slowing" yesterday.', 'She said: "growth is  slowing".')
    assert report_sup.claims[0].status == "supported"
    # Unsupported
    report_unsup = flag(
        'She said "growth is stopping" yesterday.', 'She said: "growth is  slowing".'
    )
    assert report_unsup.claims[0].status == "unsupported"
    assert report_unsup.claims[0].missing == ("growth is stopping",)


def test_acceptance_names_supported_and_unsupported():
    report_sup = flag("The deal was signed by Maria Lopez.", "Maria Lopez signed it.")
    assert report_sup.claims[0].status == "supported"
    report_unsup = flag("The deal was signed by Mario Lopez.", "Maria Lopez signed it.")
    assert report_unsup.claims[0].status == "unsupported"
    assert report_unsup.claims[0].missing == ("Mario Lopez",)


def test_acceptance_no_checkable_facts_and_ratio():
    report = flag("It went well.", "Some context.")
    assert report.claims[0].status == "no_checkable_facts"
    # Mixed report
    answer = "First supported fact 10. Second unsupported fact 20. Third no facts."
    context = "10 is here."
    mixed_report = flag(answer, context)
    assert len(mixed_report.claims) == 3
    statuses = [c.status for c in mixed_report.claims]
    assert statuses == ["supported", "unsupported", "no_checkable_facts"]
    assert mixed_report.supported_ratio == 0.5


def test_acceptance_input_too_large():
    max_chars = 100
    answer = "a" * 60
    context = "b" * 50
    with pytest.raises(FlaggerError) as exc_info:
        flag(answer, context, max_chars=max_chars)
    assert exc_info.value.code == "input_too_large"
    # Exactly at limit should be accepted
    answer = "a" * 50
    context = "b" * 50
    flag(answer, context, max_chars=100)


def test_acceptance_cli(tmp_path: Path):
    answer_file = tmp_path / "answer.txt"
    context_file = tmp_path / "ctx.txt"
    answer_file.write_text("Revenue grew 15% in 2024.")
    context_file.write_text("In 2024 revenue reached $1200, up 12%.")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unsupported_claim_flagger",
            "--context",
            str(context_file),
            str(answer_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "claims" in output
    assert "supported_ratio" in output
    # Check sorted keys by verifying first key is alphabetical? We'll just ensure it's valid JSON.
    # Missing file should return 2
    result_missing = subprocess.run(
        [
            sys.executable,
            "-m",
            "unsupported_claim_flagger",
            "--context",
            str(tmp_path / "nonexistent.txt"),
            str(answer_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result_missing.returncode == 2


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


def test_edge_number_next_to_unit():
    facts = extract_facts("It is 5km away.")
    assert any(f.kind == "number" and f.text == "5" for f in facts)


def test_edge_percent_next_to_punctuation():
    facts = extract_facts("Growth was 12%.")
    assert any(f.kind == "number" and f.text == "12%" for f in facts)


def test_edge_negative_looking_hyphenated_range():
    facts = extract_facts("Range is 3-4.")
    numbers = [f for f in facts if f.kind == "number"]
    # Should only get "3", not "4" because hyphen preceding? Actually "3" is before hyphen, allowed.
    assert len(numbers) == 1
    assert numbers[0].text == "3"
    assert numbers[0].normalized == "3"


def test_edge_date_not_double_counted_as_number():
    facts = extract_facts("Date 2026-11-09.")
    dates = [f for f in facts if f.kind == "date"]
    numbers = [f for f in facts if f.kind == "number"]
    assert len(dates) == 1
    assert dates[0].normalized == "2026-11-09"
    # The numbers 2026, 11, 09 should not be extracted because span consumed by date.
    assert all(f.text not in ("2026", "11", "09") for f in numbers)


def test_edge_curly_quotes():
    sentence = "He said “hello world” loudly."
    facts = extract_facts(sentence)
    quote_facts = [f for f in facts if f.kind == "quote"]
    assert len(quote_facts) == 1
    assert quote_facts[0].text == "hello world"
    assert quote_facts[0].normalized == "hello world"


def test_edge_empty_answer():
    report = flag("", "Some context")
    assert len(report.claims) == 0
    assert report.supported_ratio == 1.0


def test_edge_sentence_initial_capital_word_not_name():
    facts = extract_facts("The quick Brown Fox jumps.")
    names = [f for f in facts if f.kind == "name"]
    # "The" is the first word of the sentence, so it is never a name fact,
    # but the following capitalized words are.
    assert len(names) == 1
    assert names[0].text == "Brown Fox"


def test_edge_names_with_multiple_words():
    facts = extract_facts("John Smith and Mary Jane Watson went.")
    names = [f for f in facts if f.kind == "name"]
    assert any(f.text == "John Smith" for f in names)
    assert any(f.text == "Mary Jane Watson" for f in names)


def test_quote_length_limit():
    # 301 characters should be ignored
    long_quote = "a" * 301
    sentence = f'"{long_quote}" is long.'
    facts = extract_facts(sentence)
    assert not any(f.kind == "quote" for f in facts)


def test_invalid_calendar_date_ignored():
    facts = extract_facts("Date 2026-02-30.")
    assert not any(f.kind == "date" for f in facts)


def test_context_multiple_strings():
    answer = "The value is 42 and name John Doe."
    context1 = "Value is 42."
    context2 = "John Doe is here."
    report = flag(answer, [context1, context2])
    assert report.claims[0].status == "supported"


def test_name_case_sensitive():
    answer = "He is John Doe."
    context = "john doe is here."
    report = flag(answer, context)
    assert report.claims[0].status == "unsupported"


def test_quote_whitespace_collapsed_context():
    answer = 'He said "hello   world".'
    context = 'He said "hello world".'
    report = flag(answer, context)
    assert report.claims[0].status == "supported"


def test_number_comma_normalization_support():
    answer = "Amount is 1,200."
    context = "Amount is 1200."
    report = flag(answer, context)
    assert report.claims[0].status == "supported"


def test_sentence_split_decimal_not_split():
    report = flag("The price is 3.5 and 4.2.", "Context: 3.5 and 4.2")
    # Decimal points have no following whitespace, so they do not end a sentence.
    assert len(report.claims) == 1


# ---------------------------------------------------------------------------
# CLI additional tests
# ---------------------------------------------------------------------------


def test_cli_exit_code_zero_for_supported(tmp_path: Path):
    answer_file = tmp_path / "answer.txt"
    context_file = tmp_path / "ctx.txt"
    answer_file.write_text("Revenue grew 12% in 2024.")
    context_file.write_text("In 2024 revenue reached $1200, up 12%.")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unsupported_claim_flagger",
            "--context",
            str(context_file),
            str(answer_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_json_output_structure(tmp_path: Path):
    answer_file = tmp_path / "answer.txt"
    context_file = tmp_path / "ctx.txt"
    answer_file.write_text("Revenue grew 15% in 2024.")
    context_file.write_text("In 2024 revenue reached $1200, up 12%.")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unsupported_claim_flagger",
            "--context",
            str(context_file),
            str(answer_file),
        ],
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert "claims" in output
    assert "supported_ratio" in output
    assert output["supported_ratio"] == 0.0  # one unsupported claim, no supported
    claim = output["claims"][0]
    assert claim["status"] == "unsupported"
    assert claim["missing"] == ["15%"]
    # Check sorted keys by ensuring the first key in the JSON string is alphabetical? We'll just trust sort_keys=True.


def test_cli_main_supported(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    answer_file = tmp_path / "answer.txt"
    context_file = tmp_path / "ctx.txt"
    answer_file.write_text("Revenue grew 12% in 2024.")
    context_file.write_text("In 2024 revenue reached $1200, up 12%.")
    assert main(["--context", str(context_file), str(answer_file)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["supported_ratio"] == 1.0


def test_cli_main_missing_file(tmp_path: Path):
    answer_file = tmp_path / "answer.txt"
    answer_file.write_text("Revenue grew 12% in 2024.")
    missing = tmp_path / "nonexistent.txt"
    assert main(["--context", str(missing), str(answer_file)]) == 2


def test_sentence_limit():
    answer = "A. " * 2001
    with pytest.raises(FlaggerError) as exc_info:
        flag(answer, "context")
    assert exc_info.value.code == "input_too_large"
