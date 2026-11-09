# unsupported-claim-flagger

[![PyPI version](https://img.shields.io/pypi/v/trysac-unsupported-claim-flagger)](https://pypi.org/project/trysac-unsupported-claim-flagger/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-unsupported-claim-flagger)](LICENSE)
[![CI](https://github.com/Trysac/u208-unsupported-claim-flagger/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u208-unsupported-claim-flagger/actions/workflows/ci.yml)

Flag answer sentences whose numbers, dates, quotes or proper names do not appear in the supplied context, without needing citations or an LLM

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-unsupported-claim-flagger
# or
uv add trysac-unsupported-claim-flagger
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import unsupported_claim_flagger

# normalize() trims surrounding whitespace and lower-cases the text.
print(unsupported_claim_flagger.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    unsupported_claim_flagger.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
