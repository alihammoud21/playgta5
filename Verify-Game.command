#!/bin/bash
cd "$(dirname "$0")" || exit 1
bash ./mac-launcher.sh verify
status=$?
read -r -p 'Press Return to close. '
exit "$status"
