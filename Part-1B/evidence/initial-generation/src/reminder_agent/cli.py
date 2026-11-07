"""Thin CLI for ad-hoc inspection: `reminder parse "<text>" --now ... --tz ...`."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .agent import Agent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reminder", description="NL reminder parser.")
    sub = p.add_subparsers(dest="cmd", required=True)

    parse = sub.add_parser("parse", help="Parse a natural-language reminder request.")
    parse.add_argument("text")
    parse.add_argument("--now", required=True, help="Reference time, ISO 8601 UTC.")
    parse.add_argument("--tz", default="UTC", help="IANA timezone, default UTC.")
    parse.add_argument("--backend", choices=["real", "mock"], default="real")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd != "parse":
        return 2

    try:
        agent = Agent(backend_name=args.backend)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    try:
        res = agent.parse(text=args.text, now_iso=args.now, timezone=args.tz)
    except Exception as exc:  # noqa: BLE001
        print(f"backend error: {exc}", file=sys.stderr)
        return 3

    out = {
        "raw": res.call.raw_output,
        "parsed": res.parsed.model_dump() if res.parsed else None,
        "l1": [asdict(r) for r in res.l1],
        "l2": [asdict(r) for r in res.l2],
        "backend": res.call.backend,
        "model": res.call.model_id,
        "temperature": res.call.temperature,
        "prompt_hash": res.prompt_hash,
    }
    print(json.dumps(out, indent=2))
    return 0 if (res.structural_ok and res.invariants_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
