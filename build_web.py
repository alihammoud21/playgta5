"""Build a static, playable Vercel deployment from the verified public release."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from download_game import digest, extract_payload, target_path

HERE = Path(__file__).resolve().parent
PREFIX = 'mirror/playgta5.com/'


def patch_worker(code):
    old = 'if (wanted.size) await batchFetch(full, true, wanted);'
    new = 'for (const r of full) { if (wanted.has(r.id)) await ensureBlocks(r.id, r.a, r.b, true); }'
    if code.count(old) != 1:
        raise ValueError('Unrecognized I/O worker: expected exactly one batch prefetch call')
    return code.replace(old, new)


def patch_page(code):
    old = 'const q = new URLSearchParams(location.search);'
    new = old + "\n// Conservative hosted defaults; explicit URL settings still take precedence.\nfor (const [key, value] of Object.entries({low:'1', fps:'30', res:'1280x720'})) { if (!q.has(key)) q.set(key, value); }"
    if code.count(old) != 1:
        raise ValueError('Unrecognized game page: expected exactly one query parser')
    return code.replace(old, new)


def finish(output):
    page = output / 'index.html'
    page.write_text(patch_page(page.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    workers = list((output / 'b').glob('*/io_worker.js'))
    if len(workers) != 1:
        raise ValueError('Expected one versioned I/O worker')
    worker = workers[0]
    worker.write_text(patch_worker(worker.read_text(encoding='utf-8')), encoding='utf-8', newline='\n')
    help_dir = output / 'help'
    help_dir.mkdir()
    shutil.copyfile(HERE / 'public/index.html', help_dir / 'index.html')
    print('Ready: playable game at /; download/help page at /help/', flush=True)


def build(output, source=None):
    inventory = json.loads((HERE / 'file-inventory.json').read_text(encoding='utf-8'))
    manifest = json.loads((HERE / 'download-manifest.json').read_text(encoding='utf-8'))
    records = [r for r in inventory['files'] if r['path'].startswith(PREFIX)]
    if output.exists():
        raise ValueError(f'Output already exists; choose a fresh directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    if source:
        output.mkdir()
        for record in records:
            relative = record['path'][len(PREFIX):]
            original = target_path(source, relative)
            if not original.is_file() or original.stat().st_size != record['bytes'] or digest(original) != record['sha256']:
                raise ValueError(f'Source verification failed: {relative}')
            destination = target_path(output, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if relative == 'index.html' or relative.endswith('/io_worker.js'):
                shutil.copyfile(original, destination)  # Patched files must never share an inode with the original.
            else:
                try:
                    os.link(original, destination)
                except OSError:
                    shutil.copyfile(original, destination)
        print(f'Verified {len(records)} local game files.', flush=True)
    else:
        # One archive at a time keeps peak disk usage close to the 21 GB extracted game.
        with tempfile.TemporaryDirectory(prefix='game-build-', dir=output.parent) as temporary:
            stage = Path(temporary)
            for part in manifest['parts']:
                archive = target_path(stage, part['name'])
                selected = [r for r in records if r['part'] == part['name']]
                required = part['bytes'] + sum(r['bytes'] for r in selected) + 128 * 1024**2
                if shutil.disk_usage(stage).free < required:
                    raise ValueError(f'Insufficient build disk space for {part["name"]}')
                print(f'Downloading {part["name"]} ({part["bytes"]:,} bytes)', flush=True)
                subprocess.run(['curl', '--fail', '--location', '--retry', '4', '--silent', '--show-error', '--output', str(archive), part['url']], check=True)
                if archive.stat().st_size != part['bytes'] or digest(archive) != part['sha256']:
                    raise ValueError(f'Release checksum mismatch: {part["name"]}')
                extract_payload(archive, stage, selected, windows=False)
                archive.unlink()
                print(f'Verified and extracted {len(selected)} game files from {part["name"]}', flush=True)
            (stage / 'mirror/playgta5.com').rename(output)
    finish(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='verified existing playgta5.com directory (local testing)')
    parser.add_argument('--output', type=Path, default=HERE / 'web-output')
    args = parser.parse_args()
    build(args.output.resolve(), args.source.resolve() if args.source else None)
