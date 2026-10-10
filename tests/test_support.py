import gzip
import hashlib
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import download_game
import serve_local


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def archive(self, files):
        archive = self.root / 'part.zip'
        records = []
        with zipfile.ZipFile(archive, 'w') as bundle:
            for name, data in files.items():
                bundle.writestr(name, data)
                records.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        return archive, records

    def test_mac_install_preserves_updated_helpers_skips_windows_and_resumes(self):
        (self.root / 'README.md').write_text('current')
        archive, records = self.archive({'README.md': b'old', 'runtime/python.exe': b'windows', 'mirror/playgta5.com/index.html': b'game'})
        for _ in range(2):
            download_game.extract_payload(archive, self.root, records, windows=False)
        self.assertEqual((self.root / 'README.md').read_text(), 'current')
        self.assertFalse((self.root / 'runtime').exists())
        self.assertEqual((self.root / 'mirror/playgta5.com/index.html').read_bytes(), b'game')

    def test_different_existing_asset_is_not_overwritten(self):
        archive, records = self.archive({'mirror/a': b'expected'})
        (self.root / 'mirror').mkdir()
        (self.root / 'mirror/a').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Existing file differs'):
            download_game.extract_payload(archive, self.root, records)
        self.assertEqual((self.root / 'mirror/a').read_bytes(), b'changed')

    def test_traversal_and_corrupt_payload_rejected(self):
        for name in ['../escape', 'mirror/../../escape', '/absolute', 'C:/escape', 'mirror\\escape']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                download_game.target_path(self.root, name)
        archive, records = self.archive({'mirror/a': b'expected'})
        records[0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'checksum'):
            download_game.extract_payload(archive, self.root, records)
        self.assertFalse((self.root / 'mirror/a').exists())

    def test_missing_asset_rejected(self):
        archive, records = self.archive({})
        records.append({'path': 'mirror/missing', 'bytes': 1, 'sha256': '0'*64})
        with self.assertRaisesRegex(ValueError, 'missing'):
            download_game.extract_payload(archive, self.root, records)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.previous = serve_local.ROOT
        serve_local.ROOT = Path(cls.temp.name)
        (serve_local.ROOT / 'data').mkdir()
        (serve_local.ROOT / 'data/sample').write_bytes(b'0123456789')
        (serve_local.ROOT / 'index.html').write_text('game')
        cls.server = serve_local.ThreadingHTTPServer(('127.0.0.1', 0), serve_local.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        serve_local.ROOT = cls.previous
        cls.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_isolation_and_support_page(self):
        status, headers, body = self.request('GET', '/__support/')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Cross-Origin-Opener-Policy'], 'same-origin')
        self.assertEqual(headers['Cross-Origin-Embedder-Policy'], 'require-corp')
        self.assertIn(b'check.js', body)
        self.assertEqual(self.request('GET', '/__support/check.js')[0], 200)

    def test_ranges_and_unsatisfiable_range(self):
        for range_header, expected in [('bytes=2-5', b'2345'), ('bytes=-3', b'789'), ('bytes=8-', b'89')]:
            with self.subTest(range=range_header):
                status, headers, body = self.request('GET', '/data/sample', headers={'Range': range_header})
                self.assertEqual(status, 206)
                self.assertEqual(body, expected)
                self.assertEqual(int(headers['Content-Length']), len(expected))
        self.assertEqual(self.request('GET', '/data/sample', headers={'Range': 'bytes=99-'})[0], 416)

    def test_plain_and_gzip_batch(self):
        for suffix in ['', '?gz=1']:
            status, headers, body = self.request('POST', '/data/batch' + suffix, json.dumps([['sample', 2, 4], ['sample', 8, 20]]))
            self.assertEqual(status, 200)
            self.assertEqual(headers['X-Run-Lengths'], '3,2')
            self.assertEqual(gzip.decompress(body) if suffix else body, b'23489')

    def test_bad_requests_fail_without_stopping_server(self):
        for runs in [[['../index.html', 0, 3]], [[{}, 0, 3]], [['sample', '0', 3]], [['sample', -1, 3]], ['bad']]:
            self.assertEqual(self.request('POST', '/data/batch', json.dumps(runs))[0], 400)
        self.assertEqual(self.request('POST', '/data/batch', b'', {'Content-Length': '-1'})[0], 413)
        self.assertEqual(self.request('GET', '/')[0], 200)


if __name__ == '__main__':
    unittest.main()
