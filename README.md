# PlayGTA5 local browser game

Download the complete browser-game snapshot, including **all 12,482 files in the `mirror` folder**. This is a compiled client snapshot, not the original game-engine source code.

The game data is approximately **21.2 GB (19.7 GiB)**. It is included in the repository's **GitHub Release downloads**, not ordinary Git commits, because some individual game files exceed GitHub's 100 MiB Git limit. **Code → Download ZIP alone does not contain the game data.**

## Download and play on Windows

1. Click **Code → Download ZIP** on this page, then extract the ZIP completely. Or clone this repository.
2. Double-click **`Download-Game.cmd`** in the extracted folder. It downloads every game archive from [the full-game release](https://github.com/alihammoud21/playgta5/releases/tag/full-game-v1), checks SHA-256 checksums, and extracts the complete mirror and bundled Python runtime. Keep the window open until it says **Download complete**. If interrupted, run it again to resume.
3. Double-click **`Launch-Local.cmd`**. Keep its server window open while playing.
4. Your browser opens **http://localhost:8000/__support/**. Review the compatibility checks, then choose the **lower-memory 720p / 30 FPS** launch option. Choose **Story Mode** or **Sandbox Mode** in the game. If your default browser is not Chrome or Edge, paste the local address into one of them.
5. Click the game to capture the mouse and enable sound. Press **Esc** to release the mouse. Close the server window when finished.

No Python installation, Netlify account, subscription, or API key is needed on Windows. The game runs on your own computer; this repository is not an online game-hosting service.

## Download and play on Mac

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/macos/) and a current Chrome or Edge browser.
2. Download and extract this repository's ZIP. Open Terminal in the extracted folder.
3. Run `bash Download-Game.command`. All release archives are downloaded with resume support and verified with SHA-256. Only game assets are extracted on Mac; the Windows runtime and old release helpers are skipped.
4. Run `bash Launch-Local.command`. Keep Terminal open while playing. Open **http://localhost:8000/__support/** in Chrome or Edge and start with the lower-memory option.
5. Run `bash Verify-Game.command` to verify installed assets. Press **Ctrl+C** in the server terminal to stop playing.

The launch/download scripts work with native Python on both Apple Silicon and Intel; Rosetta and the Windows executable are not required. **Mac gameplay is experimental and has not been validated on Mac hardware.** A working Python server does not establish GPU/renderer compatibility. Check the browser report and share any rendering errors in the issue tracker.

For double-click launching, first run `chmod +x ./*.command` in that folder. If Finder will not open a script, use the Terminal commands above after reviewing the scripts; no system security setting needs to be disabled.

## Update an existing installation

Download the latest repository ZIP and copy its helper files **and the `support` folder** into your existing installation, replacing old helpers. Keep `mirror`, `runtime`, and your browser saves. The installer preserves current helpers instead of extracting older copies from release archives. Do not extract the original release helpers over the update.

## Requirements

- 64-bit Windows for the bundled runtime; a recent **Chrome or Edge with WebGPU and hardware acceleration** enabled.
- A capable GPU and sufficient memory. Tested locally on an RTX 3070 / 32 GB RAM computer; performance on other hardware is not guaranteed.
- About **25 GB free space** for automatic installation. Allow **45 GB** if keeping all manually downloaded ZIP files alongside the extracted game.
- Internet access for the initial roughly 21 GB download. The local game server serves the downloaded assets afterward.
- First world loading and shader preparation can take several minutes. Do not close the tab just because progress appears slow.

For lower-memory loading, try **http://localhost:8000/?low=1&fps=30&res=1280x720**. This reduces rendering load; it is a troubleshooting option, not a guaranteed fix for every GPU.

## Manual download

Open [Releases → Full game v1](https://github.com/alihammoud21/playgta5/releases/tag/full-game-v1). Download **every `playgta5-part-*.zip` file** and **`file-inventory.json`**. These are independent ZIP archives, not split fragments: extract **all** of them into the **same empty folder**, and put `file-inventory.json` there too. One archive contains the launcher and runtime; the others contain the remaining mirror files. All parts are required.

The final folder should contain:

```text
Launch-Local.cmd
Start-Local.ps1
serve_local.py
runtime/
  python.exe
mirror/
  playgta5.com/
    index.html
    b/
    data/
```

Double-click `Launch-Local.cmd`. Do not open `index.html` directly: WebGPU workers, cross-origin isolation, and game-data reads require the included HTTP server.

## Verify the files

Run **`Verify-Game.cmd`** (Windows) or **`bash Verify-Game.command`** (Mac) after installation. It checks every game asset against the published SHA-256 inventory, plus the bundled runtime on Windows. Updated helper files are deliberately excluded because the inventory describes the original release. `python3 verify_game.py --all` also checks legacy helpers and will report expected differences after an update. Verification reads about 21 GB and can take a few minutes. Release ZIP checksums are listed in `SHA256SUMS.txt`.

The downloader does not overwrite existing files with different contents. If you have modified the game, download into a new empty folder instead.

## Other operating systems

On Linux, use Python 3.11+ with `python3 download_game.py`, then `python3 serve_local.py --open`. Browser/GPU support varies; Linux gameplay has not been validated. The bundled `runtime/python.exe` is Windows-only.

## Vercel and online hosting

[playgta5-tawny.vercel.app](https://playgta5-tawny.vercel.app/) is the **download and support page**, not a hosted game session. The repository's `vercel.json` serves `public/` with no build or install command; use the repository root as Vercel's Root Directory and the **Other** framework preset. The previous Git import returned 404 because there was no homepage in the deployment output.

The complete playable game cannot be deployed by simply importing this repo: its roughly 21 GB of data lives in GitHub Releases, and gameplay needs byte-range responses, COOP/COEP isolation headers, and the `/data/batch` POST protocol implemented by `serve_local.py`. Vercel's [CLI upload limits](https://vercel.com/docs/limits#static-file-uploads) and [function payload limits](https://vercel.com/docs/functions/limitations) also make a direct upload/serverless conversion unsuitable for this package. A hosted playable version needs separately provisioned asset storage and a compatible backend; that is not provided by this static page.

## Troubleshooting

- **Missing mirror / blank page:** finish downloading and extracting every release part. Run `Verify-Game.cmd`.
- **Address already in use:** another server is using port 8000. Use its existing tab, close that server, or run `runtime\python.exe serve_local.py --port 8001 --open`.
- **WebGPU unavailable:** update Chrome/Edge and your graphics driver; enable browser hardware acceleration.
- **Out of memory / tab crash:** close other tabs and applications, then try the lower-memory URL above.
- **Graphics device lost / `DXGI_ERROR_DEVICE_HUNG`:** this reports a GPU device failure. Close all game tabs, stop the game server with Ctrl+C, then restart once. Update the browser and GPU driver (macOS updates include its drivers), and check `chrome://gpu` or `edge://gpu` for hardware acceleration and Problems Detected. Try the lower-memory 720p link. Do not change Windows TDR registry settings or enable unsafe browser flags. If it persists, post your GPU model, OS/browser versions, when it happens, and the first console error to [issue #1](https://github.com/alihammoud21/playgta5/issues/1). The exact cause is still under investigation.
- **Black world but audio/map/menu work:** verify the files, try the lower-memory link, and compare Story and Sandbox. Open developer tools (F12 on Windows, Option+Command+I on Mac), capture the first shader/WebGPU error and any failed asset request, and post them with the compatibility report to [issue #2](https://github.com/alihammoud21/playgta5/issues/2). HUD rendering alone does not prove that world rendering is working. Do not delete saves as a first troubleshooting step.
- **Download failure:** rerun `Download-Game.cmd`. Completed, verified archives are remembered. Available disk space and network restrictions can affect downloading.
- **Windows security warning:** inspect the scripts and files before choosing to run them. Do not disable antivirus or system-wide security settings.

The compatibility page checks basic WebGPU device creation, shared-memory/isolation support, and a four-byte range read of the real WebAssembly file. It does **not** test every shader or certify gameplay. Diagnostics stay in your browser until you choose to copy and share them. See [Chrome's WebGPU troubleshooting guide](https://developer.chrome.com/docs/web-platform/webgpu/troubleshooting-tips) for browser checks.

## Development checks

Run `python3 -m unittest discover -s tests -v`, `node --check support/check.js`, and `bash -n mac-launcher.sh`. Tests cover installer preservation/resume, checksums, unsafe paths, isolation headers, range reads, both batch formats, and malformed requests. An existing mirror can be tested without copying it: `python3 serve_local.py --root /path/to/playgta5.com --port 8001 --open`.

## Scope and provenance

This package contains only the original local game mirror, a local server, launch/download/verification scripts, and a minimal Python runtime. It does **not** contain hosting credentials, Netlify/Cloudflare configuration, personal saved games, Ollama, or the unfinished police-mode experiment. The double-nested source mirror folder is normalized to `mirror/playgta5.com` without changing its contents.

This package is not affiliated with or endorsed by Rockstar Games, Take-Two, or that project's authors.

Game names, artwork, audio, and other game assets remain the property of their respective rights holders. No ownership or redistribution license for those assets is claimed here. Availability is subject to rights-holder requests and GitHub's policies. The bundled Python runtime retains its license in `runtime/LICENSE.txt`.
