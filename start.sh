#!/bin/sh
set -eu
ATLAS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Install Python 3.10 or newer, then run: sh start.sh"
  exit 1
fi
python3 -c 'import sys; sys.exit("Python 3.10 or newer is required") if sys.version_info < (3,10) else None'
exec python3 "$ATLAS_ROOT/server.py" "$@"
