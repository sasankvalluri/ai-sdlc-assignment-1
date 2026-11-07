#!/usr/bin/env bash
# Thin wrapper so evaluators can invoke the harness with one command.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/.."
exec uv run python .harness/run.py "$@"
