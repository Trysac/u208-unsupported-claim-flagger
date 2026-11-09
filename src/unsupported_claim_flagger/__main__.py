"""Command-line interface for unsupported_claim_flagger."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import FlaggerError, flag


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m unsupported_claim_flagger",
        description="Flag unsupported claims in an answer file against context files.",
    )
    parser.add_argument(
        "--context",
        action="append",
        required=True,
        help="Path to a context file; may be repeated.",
    )
    parser.add_argument(
        "answer",
        help="Path to the answer file.",
    )
    args = parser.parse_args(argv)

    try:
        answer_text = Path(args.answer).read_text(encoding="utf-8")
        context_texts = [Path(ctx).read_text(encoding="utf-8") for ctx in args.context]
    except OSError as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 2

    try:
        report = flag(answer_text, context_texts)
    except FlaggerError as e:
        print(f"Error: {e.code}", file=sys.stderr)
        return 2

    report_dict = {
        "claims": [
            {
                "index": claim.index,
                "sentence": claim.sentence,
                "status": claim.status,
                "facts": [
                    {
                        "kind": fact.kind,
                        "text": fact.text,
                        "normalized": fact.normalized,
                    }
                    for fact in claim.facts
                ],
                "missing": list(claim.missing),
            }
            for claim in report.claims
        ],
        "supported_ratio": report.supported_ratio,
    }
    print(json.dumps(report_dict, sort_keys=True))

    if any(c.status == "unsupported" for c in report.claims):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
