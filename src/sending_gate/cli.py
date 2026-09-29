from __future__ import annotations

import json
import sys
from pathlib import Path

from .gate import evaluate_batch


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: python -m sending_gate <rows.json> [--include-flag]", file=sys.stderr)
        return 2
    path = Path(args[0])
    include_flag = "--include-flag" in args
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "rows" in data:
        rows = data["rows"]
    elif isinstance(data, list):
        rows = data
    else:
        print("JSON must be a list of rows or {\"rows\": [...]}", file=sys.stderr)
        return 2

    report = evaluate_batch(rows)
    print(json.dumps(report, indent=2))
    allowed = [
        r
        for r in report["results"]
        if r["verdict"] == "PASS" or (include_flag and r["verdict"] == "FLAG")
    ]
    print(
        f"summary: PASS={report['counts']['PASS']} "
        f"FLAG={report['counts']['FLAG']} FAIL={report['counts']['FAIL']} "
        f"allowed={len(allowed)}",
        file=sys.stderr,
    )
    return 0 if report["counts"]["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
