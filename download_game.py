"""Install verified release payloads on macOS, Linux, or Windows (Python 3.11+)."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def payload(name, windows=None):
    if windows is None:
        windows = os.name == 'nt'
    return name.startswith('mirror/') or (windows and name.startswith('runtime/'))


def target_path(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe archive path: {name}')
    target = (root / name).resolve()
    if not target.is_relative_to(root.resolve()) or target == root.resolve():
        raise ValueError(f'Unsafe archive path: {name}')
    return target


def extract_payload(archive, root, records, windows=None):
    """Never replace current repo helpers with the older helpers inside a release."""
    expected = {r['path']: r for r in records if payload(r['path'], windows)}
    seen = set()
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            target = target_path(root, entry.filename)
            if not payload(entry.filename, windows):
                continue
            record = expected.get(entry.filename)
            if record is None or entry.filename in seen or entry.is_dir():
                raise ValueError(f'Unexpected archive entry: {entry.filename}')
            seen.add(entry.filename)
            if entry.file_size != record['bytes']:
                raise ValueError(f'Wrong archive entry size: {entry.filename}')
            if target.exists():
                if target.is_file() and digest(target) == record['sha256']:
                    continue
                raise ValueError(f'Existing file differs; not overwritten: {target}. Use a new folder or move this file aside and retry.')
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.installing')
            if temporary.is_symlink():
                raise ValueError(f'Unsafe temporary path: {temporary}')
            with bundle.open(entry) as source, temporary.open('wb') as output:
                shutil.copyfileobj(source, output, 1024 * 1024)
            if digest(temporary) != record['sha256']:
                raise ValueError(f'Extraction checksum mismatch: {target}')
            temporary.replace(target)
    if seen != set(expected):
        raise ValueError('Archive is missing expected game files')


def install(root):
    manifest = json.loads((HERE / 'download-manifest.json').read_text(encoding='utf-8'))
    inventory = json.loads((HERE / 'file-inventory.json').read_text(encoding='utf-8'))
    if not shutil.which('curl'):
        raise ValueError('curl is required (included with macOS and modern Windows).')
    root.mkdir(parents=True, exist_ok=True)
    cache = root / '.downloads'
    cache.mkdir(exist_ok=True)
    receipts = root / '.installed-parts'
    receipts.mkdir(exist_ok=True)
    for part in manifest['parts']:
        records = [r for r in inventory['files'] if r['part'] == part['name']]
        selected = [r for r in records if payload(r['path'])]
        receipt = target_path(receipts, part['name'] + '.sha256')
        if receipt.is_file() and receipt.read_text().strip() == part['sha256']:
            if all(target_path(root, r['path']).is_file() and target_path(root, r['path']).stat().st_size == r['bytes'] for r in selected):
                print('Already installed:', part['name'], flush=True)
                continue
        archive = target_path(cache, part['name'])
        partial = archive.with_suffix(archive.suffix + '.partial')
        remaining = sum(r['bytes'] for r in selected if not target_path(root, r['path']).exists())
        download_bytes = 0 if archive.exists() else max(0, part['bytes'] - (partial.stat().st_size if partial.exists() else 0))
        if shutil.disk_usage(root).free < remaining + download_bytes + 256 * 1024**2:
            raise ValueError('Not enough disk space for the next archive and its extracted files.')
        if not archive.exists():
            print('Downloading:', part['name'], flush=True)
            subprocess.run(['curl', '--fail', '--location', '--retry', '4', '--continue-at', '-', '--output', str(partial), part['url']], check=True)
            if partial.stat().st_size != part['bytes'] or digest(partial) != part['sha256']:
                raise ValueError(f'Checksum mismatch. Move aside {partial} and retry.')
            partial.replace(archive)
        if archive.stat().st_size != part['bytes'] or digest(archive) != part['sha256']:
            raise ValueError(f'Checksum mismatch: {archive}')
        print('Extracting:', part['name'], flush=True)
        extract_payload(archive, root, records)
        receipt.write_text(part['sha256'], encoding='utf-8')
        archive.unlink()  # Only this verified installer cache archive.
    print('Download complete. Run Launch-Local.command (Mac) or Launch-Local.cmd (Windows).')


if __name__ == '__main__':
    if sys.version_info < (3, 11):
        raise SystemExit('Python 3.11 or newer is required.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        install(HERE)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as error:
        raise SystemExit(f'Installation stopped: {error}\nRun again to resume; existing game files are not overwritten.')
