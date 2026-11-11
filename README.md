# trysac-unsupported-claim-flagger

[![PyPI](https://img.shields.io/pypi/v/trysac-unsupported-claim-flagger.svg)](https://pypi.org/project/trysac-unsupported-claim-flagger/)
[![Python](https://img.shields.io/pypi/pyversions/trysac-unsupported-claim-flagger.svg)](https://pypi.org/project/trysac-unsupported-claim-flagger/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LLM answers built from a context can contain a wrong figure, a date that is not in the context, a misquoted phrase, or a name that is never mentioned. `unsupported_claim_flagger` extracts checkable atoms (dates, quotes, numbers, names) from each answer sentence and checks each atom literally against the supplied context. It does not need citations and does not call an LLM.

## Installation

```bash
pip install trysac-unsupported-claim-flagger
```

## Usage

```python
from unsupported_claim_flagger import flag

answer = "Revenue grew 15% in 2024."
context = "In 2024 revenue reached $1200, up 12%."
report = flag(answer, context)
print(report.claims[0].status)  # 'unsupported'
print(report.claims[0].missing)  # ('15%',)
```

## API

### `flag(answer, context, *, max_chars=200_000)`

Returns a `Report` with a `claims` tuple and `supported_ratio`. `context` may be a string or a sequence of strings. Each `Claim` has `index`, `sentence`, `status`, `facts`, and `missing`.

A claim is `supported` when all of its facts are found in the context, `unsupported` when any fact is missing, and `no_checkable_facts` when it has no extracted facts. `missing` lists fact texts in sentence order. `supported_ratio` is `supported / (supported + unsupported)`, is `1.0` when that denominator is 0, and is rounded to 6 decimals.

Dates are supported by normalized date value; numbers by normalized number value; quotes by whitespace-collapsed substring; names by case-sensitive word-boundary match in the whitespace-collapsed context. The context is extracted with the same fact rules.

Limits and options: `max_chars` defaults to `200_000` and applies to `len(answer) + sum(len(c) for c in contexts)`. `flag` also raises if the answer has more than 2000 sentences.

Errors: `FlaggerError` has a `code` of `'input_too_large'` or `'invalid_input'`. `flag` raises `'input_too_large'` when the total character limit or the sentence limit is exceeded. Messages do not contain the input texts.

### `extract_facts(sentence)`

Extracts `Fact` objects (`kind`, `text`, `normalized`) from a sentence. Extraction order is dates, quotes, numbers, names; each character span is consumed once. Dates are ISO `YYYY-MM-DD`, `D Month YYYY`, or `Month D, YYYY` and normalize to `YYYY-MM-DD`; invalid calendar dates are ignored. Quotes are straight or curly double-quoted text of 1-300 characters and collapse whitespace. Numbers skip digit runs glued to a preceding letter, hyphen, dot, or comma; group commas and trailing decimal zeros are removed while `%` is kept. Names are 1-4 capitalized words; a single-word sequence that is the first word of the sentence is not a name.

## CLI

```bash
python -m unsupported_claim_flagger --context ctx.txt --context ctx2.txt answer.txt
```

`--context` may be repeated. The command prints the report as JSON with sorted keys. Exit codes: 0 if all claims are supported or have no checkable facts, 1 if any claim is unsupported, 2 for usage or I/O errors.

## Why not citation checkers or an LLM judge

Citation checkers only work when the model cites sources, and LLM judges are slow and non-deterministic. This library needs no citations, is deterministic, and the report names the exact missing atom. Paraphrase and semantic entailment are out of scope; pair it with an LLM judge when those are required.

## Development

Run `pytest` from the repository root. Tests live in `tests/test_flagger.py`. See [docs/SECURITY.md](docs/SECURITY.md) for the threat model.

## License

MIT
