#!/bin/sh
ATLAS_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sh "$ATLAS_ROOT/start.sh" "$@"
