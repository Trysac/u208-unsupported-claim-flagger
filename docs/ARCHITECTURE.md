# Architecture

## Overview

`unsupported_claim_flagger` is a deterministic fact extraction and literal verification library. It processes each answer sentence, extracts checkable facts (dates, numbers, quotes, names), and verifies each fact against a context, without requiring citations or an LLM judge.

## Design decisions

- **Fact extraction order**: Dates, quotes, numbers, names. Each span is consumed once to prevent double counting.
- **Normalization**: Facts are normalized (e.g., dates to ISO format, numbers stripped of commas and trailing decimal zeros, quotes whitespace-collapsed) to enable literal matching.
- **Support criteria**: A fact is supported if its normalized value appears in the context (for dates/numbers), as a substring for quotes (whitespace-collapsed), or with word boundaries for names (case-sensitive).
- **Determinism**: No randomness or external services; all operations are pure functions on strings.

See [docs/decisions/](decisions/) for recorded ADRs.
