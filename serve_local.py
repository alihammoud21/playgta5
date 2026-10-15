"""Local mirror server: isolation headers, byte ranges, and engine batch I/O."""
import argparse, gzip, io, json, mimetypes, re, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs

ROOT = Path(__file__).resolve().parent / 'mirror' / 'playgta5.com'
SUPPORT = Path(__file__).resolve().parent / 'support'
if not (ROOT / 'index.html').is_file():
    nested_root = ROOT.parent / 'mirror' / 'playgta5.com'
    if (nested_root / 'index.html').is_file():
        ROOT = nested_root
mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('text/javascript', '.js')

def improve_game_page(code):
    """Improve the launcher at serving/build time, preserving verified release files."""
    if 'game-progress' not in code:
        return code
    query = 'const q = new URLSearchParams(location.search);'
    code = code.replace(query, query + '''
// Avoid native Retina render targets and excessive worker/scene load on Macs.
// iPads can report MacIntel; they must still follow the mobile capability checks.
if (/Mac/.test(navigator.platform) && !(navigator.maxTouchPoints > 1)) {
    for (const [key, value] of Object.entries({low:'1', fps:'60', res:'1280x720', shadows:'0'})) {
        if (!q.has(key) && !(key === 'res' && q.has('scale'))) q.set(key, value);
    }
}
''', 1)
    # The upstream 1 ms tick works around Windows timer rounding, not macOS.
    code = code.replace('setInterval(() => {}, 1);',
                        "if (/^Win/.test(navigator.platform)) setInterval(() => {}, 1);", 1)
    if 'name="viewport"' not in code:
        code = code.replace('<head>', '<head><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">', 1)
    # Mobile taps must not call an absent pointer-lock API. Relative camera input
    # comes from the touch pad instead; desktop pointer lock remains unchanged.
    code = code.replace('if (!locked()) { canvas.requestPointerLock({ unadjustedMovement: true }).catch(() => canvas.requestPointerLock()); }',
                        'if (!locked() && canvas.requestPointerLock && !matchMedia("(pointer:coarse)").matches) { Promise.resolve(canvas.requestPointerLock({ unadjustedMovement: true })).catch(() => Promise.resolve(canvas.requestPointerLock()).catch(() => {})); }')
    code = code.replace(': the device may be out of memory. Close other tabs, or reload.',
                        ': loading has paused. Use Help / browser checks and collect the first console error.')
    code = code.replace('If the tab shows "Aw, Snap!" or SIGILL it ran out of memory.',
                        'A tab crash needs its error details; it does not by itself prove insufficient RAM.')
    link = (SUPPORT / 'overlay.html').read_text(encoding='utf-8')
    marker = 'Atomics.store(w, MY, H >> 1);'
    if code.count(marker) == 1:
        code = code.replace('<head>', '<head><script src="/__support/controller.js"></script><script defer src="/__support/touch.js"></script>', 1)
        code = code.replace(marker, marker + '''
if (!window.PlayGTA5Enhanced) {
    const mode = document.createElement('button');
    mode.setAttribute('data-game-overlay', '');
    mode.title = 'Click to switch on-foot/driving controls; View + Menu also switches';
    mode.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:10003;max-width:48vw;min-height:44px;padding:10px 14px;background:#182621e8;color:white;border:1px solid #789184;border-radius:24px;font:14px system-ui;cursor:pointer';
    mode.hidden = true;
    document.body.append(mode);
    const controller = PlayGTA5Controller.attach({keys,w,VK,canvas,status:text => {
        mode.hidden = text === 'Press a controller button to connect';
        if (mode.textContent !== text) mode.textContent = text;
    }});
    mode.onclick = () => controller.toggleMode();
}
''', 1)
    return code.replace('<body>', '<body>\n' + link, 1)

class Handler(SimpleHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(30)

    def __init__(self, *args, **kwargs):
        self.byte_range = None
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def send_head(self):
        self.byte_range = None
        if urlsplit(self.path).path in ('/', '/index.html') and (ROOT / 'index.html').is_file():
            body = improve_game_page((ROOT / 'index.html').read_text(encoding='utf-8')).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return io.BytesIO(body)
        support_files = {'/__support/': 'index.html', '/__support/check.js': 'check.js', '/__support/controller.js': 'controller.js', '/__support/touch.js': 'touch.js'}
        support_name = support_files.get(urlsplit(self.path).path)
        if support_name:
            path = SUPPORT / support_name
            if not path.is_file():
                self.send_error(404)
                return None
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(str(path)))
            self.send_header('Content-Length', str(path.stat().st_size))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return path.open('rb')
        if not self.headers.get('Range'):
            return super().send_head()
        path = Path(self.translate_path(self.path))
        if not path.is_file():
            self.send_error(404)
            return None
        size = path.stat().st_size
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', self.headers['Range'])
        if not match or not any(match.groups()):
            self.send_error(416)
            return None
        start = int(match[1]) if match[1] else max(0, size - int(match[2]))
        end = min(size - 1, int(match[2])) if match[1] and match[2] else size - 1
        if start >= size or end < start:
            self.send_response(416)
            self.send_header('Content-Range', 'bytes */%d' % size)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return None
        self.byte_range = (start, end)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(str(path)))
        self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        source = path.open('rb')
        source.seek(start)
        return source

    def copyfile(self, source, outputfile):
        if self.byte_range is None:
            return super().copyfile(source, outputfile)
        remaining = self.byte_range[1] - self.byte_range[0] + 1
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    def do_POST(self):
        url = urlsplit(self.path)
        if url.path != '/data/batch':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400, 'Invalid Content-Length')
            return
        if not 0 <= length <= 1024 * 1024:
            self.send_error(413, 'Invalid batch size')
            return
        try:
            runs = json.loads(self.rfile.read(length))
            if not isinstance(runs, list) or len(runs) > 1000:
                raise ValueError('invalid batch')
            selected = []
            data_root = (ROOT / 'data').resolve()
            for name, start, end in runs:
                if not isinstance(name, str) or type(start) is not int or type(end) is not int:
                    raise ValueError('invalid file/range types')
                file = (data_root / name).resolve()
                if not file.is_relative_to(data_root) or start < 0 or end < start:
                    raise ValueError('invalid file/range')
                selected.append((file, start, max(0, min(end + 1, file.stat().st_size) - start)))
            total = sum(n for _, _, n in selected)
            if total > 64 * 1024 * 1024:
                raise ValueError('batch exceeds 64 MiB')
            output = io.BytesIO()
            for file, start, n in selected:
                with file.open('rb') as source:
                    source.seek(start)
                    output.write(source.read(n))
            body = output.getvalue()
            compressed = parse_qs(url.query).get('gz') == ['1']
            if compressed:
                body = gzip.compress(body, compresslevel=1)
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Run-Lengths', ','.join(str(n) for _, _, n in selected))
            if compressed:
                self.send_header('Content-Encoding', 'gzip')
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, TypeError, OSError) as exc:
            self.send_error(400, str(exc))

if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--port', type=int, default=8000)
    args.add_argument('--root', type=Path, help='existing game directory containing index.html, b/, and data/')
    args.add_argument('--open', action='store_true', help='open browser compatibility and launch page')
    options = args.parse_args()
    if options.root:
        ROOT = options.root.resolve()
    if not (ROOT / 'index.html').is_file():
        args.error('Game files are missing. Run Download-Game.cmd (Windows) or Download-Game.command (Mac) first.')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', options.port), Handler)
    except OSError as error:
        args.error(f'Cannot start on port {options.port}: {error}. Close the previous game server with Ctrl+C, or choose --port 8001.')
    address = 'http://localhost:%d/' % server.server_port
    print('Local mirror: %s (Ctrl+C to stop)' % address, flush=True)
    if options.open:
        webbrowser.open(address + '__support/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
