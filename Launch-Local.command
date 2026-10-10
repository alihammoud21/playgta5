#!/bin/bash
cd "$(dirname "$0")" || exit 1
bash ./mac-launcher.sh launch
status=$?
if [ "$status" -ne 0 ]; then read -r -p 'Press Return to close. '; fi
exit "$status"
