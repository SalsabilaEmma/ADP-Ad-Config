#!/bin/sh
# Usage: new-app.sh <package> [everyNTaps=10] [cooldownSec=30]
set -eu
if [ $# -lt 1 ] || [ $# -gt 3 ]; then
  echo "usage: $0 <package> [everyNTaps=10] [cooldownSec=30]" >&2
  exit 2
fi
PKG=$1
TAPS=${2:-10}
COOL=${3:-30}
ROOT=$(cd "$(dirname "$0")/.." && pwd)
FILE="$ROOT/v1/$PKG.json"

if ! printf '%s' "$PKG" | grep -Eq '^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$'; then
  echo "ERROR: invalid package: $PKG" >&2
  exit 1
fi
for n in "$TAPS" "$COOL"; do
  if ! printf '%s' "$n" | grep -Eq '^[0-9]{1,6}$'; then
    echo "ERROR: not an integer: $n" >&2
    exit 1
  fi
done
if [ -e "$FILE" ]; then
  echo "ERROR: already exists: $FILE" >&2
  exit 1
fi

mkdir -p "$ROOT/v1"
cat > "$FILE" <<JSON
{
  "schema": 1,
  "ads": {
    "appOpen": {
      "enabled": true,
      "unitId": "ca-app-pub-3940256099942544/9257395921"
    },
    "banner": {
      "enabled": true,
      "unitId": "ca-app-pub-3940256099942544/9214589741"
    },
    "interstitial": {
      "enabled": true,
      "unitId": "ca-app-pub-3940256099942544/1033173712",
      "everyNTaps": $((TAPS + 0)),
      "cooldownSec": $((COOL + 0))
    },
    "native": {
      "enabled": true,
      "unitId": "ca-app-pub-3940256099942544/2247696110"
    }
  }
}
JSON

if python3 "$ROOT/scripts/validate.py" "$FILE"; then
  echo "created: $FILE"
else
  rm -f "$FILE"
  echo "ERROR: generated file invalid, removed" >&2
  exit 1
fi
