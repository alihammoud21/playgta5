#!/bin/bash
set -eu
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
  echo 'Install Python 3.11 or newer from https://www.python.org/downloads/macos/ and try again.'
  exit 1
fi
case "${1:-launch}" in
  download) exec python3 download_game.py ;;
  verify) exec python3 verify_game.py ;;
  launch) exec python3 serve_local.py --open ;;
  *) echo 'Expected download, verify, or launch'; exit 2 ;;
esac
