"""Verify downloaded game files without changing them."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
inventory = json.loads((root / 'file-inventory.json').read_text(encoding='utf-8'))
failures = []
for index, record in enumerate(inventory['files'], 1):
    path = root / record['path']
    try:
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
        print(f"Checked {index}/{len(inventory['files'])}", flush=True)
print(f"Checked {len(inventory['files'])} files; {len(failures)} failed.")
raise SystemExit(bool(failures))
