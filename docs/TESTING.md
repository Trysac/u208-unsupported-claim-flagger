# Testing

Run the test suite with:

```bash
pytest
```

## Test structure

All tests are in `tests/test_flagger.py`. The file imports `FlaggerError`, `extract_facts`, `flag`, and `main` from `unsupported_claim_flagger`.

The test functions are:

- `test_acceptance_supported_number_percent`: checks a supported percent and number against context.
- `test_acceptance_unsupported_percent`: checks an unsupported percent and the `missing` value.
- `test_acceptance_extract_facts_numbers`: checks number extraction next to units and inside `COVID-19`.
- `test_acceptance_extract_facts_commas_and_decimals`: checks `1,000,000` and `10.0` normalization.
- `test_acceptance_dates_supported_both_formats`: checks ISO dates against `9 November 2026` and `November 9, 2026` context formats.
- `test_acceptance_quotes_supported_and_unsupported`: checks whitespace-collapsed quote support and missing quote text.
- `test_acceptance_names_supported_and_unsupported`: checks name support, an unsupported name, and that sentence-initial `The` is not a name fact.
- `test_acceptance_no_checkable_facts_and_ratio`: checks `no_checkable_facts`, the supported ratio calculation, and `input_too_large` at the character limit.
- `test_acceptance_cli`: runs the module with `--context`, checks JSON output and exit codes, and checks exit code 2 for a missing file.
