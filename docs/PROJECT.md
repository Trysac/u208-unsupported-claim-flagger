# Project

## Name

trysac-unsupported-claim-flagger

## Description

Flag answer sentences whose numbers, dates, quotes or proper names do not appear in the supplied context, without needing citations or an LLM.

## Objective

Provide a deterministic, dependency-free library that splits an answer into sentences, extracts checkable facts (dates, quotes, numbers, names), and verifies each fact literally against the supplied context. The report identifies each sentence as `supported`, `unsupported`, or `no_checkable_facts`, lists missing fact texts, and gives a supported ratio.

## Scope

- Public library API: `flag`, `extract_facts`, `Report`, `Claim`, `Fact`, and `FlaggerError`.
- Fact kinds: ISO and English-month dates, straight or curly double-quoted text, numbers with optional thousands separators and `%`, and 1-4 capitalized-word names.
- Literal support checks against one context string or a sequence of context strings.
- Input limits: total answer plus context length up to `max_chars` (default `200_000`) and at most 2000 answer sentences.
- CLI: `python -m unsupported_claim_flagger` with repeatable `--context` and JSON output.

## Out of scope

- Paraphrase, semantic entailment, negation, and coreference resolution.
- Citation checking and LLM judging.
- Non-English number and date formats.
- Redaction or semantic validation of the report contents.

## Category

A. LLM engineering

## Demo

terminal

## License

MIT

## Factory run u208 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-09 | generation | deepseek-v4-pro | yes | 1633 | 16626 | 0 | 3328 | 0.0341 |
| 2026-11-09 | fix-1 | deepseek-flash | no | 35399 | 34838 | 0 | 869504 | 0.0288 |
| 2026-11-09 | fix-2 | deepseek-flash | no | 62788 | 25008 | 0 | 1335168 | 0.0284 |
| 2026-11-09 | fix-3 | deepseek-flash | no | 16805 | 15122 | 0 | 262656 | 0.0124 |
| 2026-11-09 | fix-4 | deepseek-flash | no | 60620 | 32261 | 0 | 995200 | 0.0314 |
| 2026-11-09 | audit | deepseek-flash | no | 33557 | 40985 | 0 | 501376 | 0.0311 |
| 2026-11-09 | docs | deepseek-flash | no | 103483 | 6012 | 0 | 256 | 0.0191 |

Total: $0.1854. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
