# Security

## Threat model

This library processes untrusted answer and context strings in memory. It does not fetch URLs, execute code, or call external services.

Defended:

- Oversized input is bounded: `flag` raises `FlaggerError` with code `input_too_large` when `len(answer) + sum(len(c) for c in contexts)` exceeds `max_chars` (default `200_000`) or when the answer has more than 2000 sentences.
- Error messages use the error code and do not include the answer or context texts.
- The package logger uses `logging.getLogger(__name__)` with a `NullHandler`; the library does not log input text.
- Quote extraction accepts at most 300 characters per quote, and extraction uses fixed regular expressions rather than user-supplied patterns.

Not defended:

- No authentication, authorization, encryption, network isolation, or sandbox is provided; the library is an in-process text checker.
- The CLI prints the report, including sentence text and missing fact text, to stdout. The library does not redact PII or secrets from that output.
- The library does not prove semantic correctness. It only compares extracted atoms literally, so unextracted facts, paraphrases, negation, coreference, and non-English formats can be missed.

## Input validation

- Total character limit and sentence count limit are enforced before claim processing; exceeding either raises `FlaggerError` with code `input_too_large`.
- Invalid calendar dates are ignored during date extraction rather than raising an error.
- Quotes shorter than 1 character or longer than 300 characters are not extracted.
- The CLI reads files as UTF-8 and returns exit code 2 for file read errors or `FlaggerError`.
