"""Verify downloaded game files without changing them."""
import hashlib
import json
import argparse
import os
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--all', action='store_true', help='also compare legacy helper files against the original release (updated helpers will differ)')
options = parser.parse_args()
root = options.root.resolve()
inventory = json.loads((Path(__file__).resolve().parent / 'file-inventory.json').read_text(encoding='utf-8'))
records = [r for r in inventory['files'] if options.all or r['path'].startswith('mirror/') or (os.name == 'nt' and r['path'].startswith('runtime/'))]
failures = []
for index, record in enumerate(records, 1):
    path = (root / record['path']).resolve()
    try:
        if not path.is_relative_to(root):
            raise ValueError('unsafe inventory path')
        if not path.is_file() or path.stat().st_size != record['bytes']:
            raise ValueError('missing file or wrong size')
        with path.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        if digest != record['sha256']:
            raise ValueError('SHA-256 mismatch')
    except (OSError, ValueError) as error:
        failures.append(record['path'])
        print(f"FAIL {record['path']}: {error}", flush=True)
    if index % 500 == 0:
        print(f"Checked {index}/{len(records)}", flush=True)
print(f"Checked {len(records)} files; {len(failures)} failed.")
raise SystemExit(bool(failures))
