"""Exercise the real PowerShell installer using a tiny, already-downloaded release."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile


@unittest.skipUnless(os.name == 'nt', 'PowerShell installer is Windows-only')
class WindowsInstallerTests(unittest.TestCase):
    def test_updated_helpers_and_separate_destination(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installer = root / 'installer'
            target = root / 'destination'
            installer.mkdir()
            (target / '.downloads').mkdir(parents=True)
            helpers = ['Launch-Local.cmd', 'Start-Local.ps1', 'serve_local.py', 'Verify-Game.cmd', 'verify_game.py', 'README.md', 'Download-Game.cmd', 'Download-Game.ps1', 'support/index.html', 'support/check.js']
            for name in helpers:
                path = installer / name
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / name, path)
            name = 'test-part.zip'
            archive = target / '.downloads' / name
            records = []
            files = {'README.md': b'legacy readme', 'serve_local.py': b'legacy server', 'mirror/playgta5.com/index.html': b'test game', 'runtime/python.exe': b'test runtime'}
            with zipfile.ZipFile(archive, 'w') as bundle:
                for path, data in files.items():
                    bundle.writestr(path, data)
                    records.append({'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'part': name})
            manifest = {'parts': [{'name': name, 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'url': 'https://example.invalid/must-not-download'}]}
            (installer / 'download-manifest.json').write_text(json.dumps(manifest))
            (installer / 'file-inventory.json').write_text(json.dumps({'files': records}))
            command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(installer / 'Download-Game.ps1'), '-Destination', str(target)]
            for _ in range(2):
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((target / 'serve_local.py').read_bytes(), (source / 'serve_local.py').read_bytes())
            self.assertEqual((target / 'README.md').read_bytes(), (source / 'README.md').read_bytes())
            self.assertEqual((target / 'support/check.js').read_bytes(), (source / 'support/check.js').read_bytes())
            self.assertEqual((target / 'mirror/playgta5.com/index.html').read_bytes(), b'test game')
            self.assertFalse(archive.exists())


if __name__ == '__main__':
    unittest.main()
