# Deterministic atom extraction and literal verification for claim flagging

Status: accepted (generated, pending human review)

## Context

Need to flag unsupported claims in LLM answers without citations or LLM judges. The solution must be fast, deterministic, and have no external dependencies.

## Decision

Extract checkable facts (dates, numbers, quotes, names) from each sentence and verify each fact literally against the context. Use a defined extraction order to avoid double counting and normalize facts for matching.

## Consequences

The package is deterministic and dependency-free. However, it only performs literal matching, so paraphrase or semantic entailment is out of scope. It supports English date and number formats as specified.
