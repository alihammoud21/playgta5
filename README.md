# PlayGTA5 local browser game

Download the complete browser-game snapshot, including **all 12,482 files in the `mirror` folder**. This is a compiled client snapshot, not the original game-engine source code.

The game data is approximately **21.2 GB (19.7 GiB)**. It is included in the repository's **GitHub Release downloads**, not ordinary Git commits, because some individual game files exceed GitHub's 100 MiB Git limit. **Code → Download ZIP alone does not contain the game data.**

## Download and play on Windows

1. Click **Code → Download ZIP** on this page, then extract the ZIP completely. Or clone this repository.
2. Double-click **`Download-Game.cmd`** in the extracted folder. It downloads every game archive from [the full-game release](https://github.com/alihammoud21/playgta5/releases/tag/full-game-v1), checks SHA-256 checksums, and extracts the complete mirror and bundled Python runtime. Keep the window open until it says **Download complete**. If interrupted, run it again to resume.
3. Double-click **`Launch-Local.cmd`**. Keep its server window open while playing.
4. Your browser opens **http://localhost:8000/**. Choose **Story Mode** or **Sandbox Mode**. If the browser does not open automatically, paste that address into Chrome or Edge.
5. Click the game to capture the mouse and enable sound. Press **Esc** to release the mouse. Close the server window when finished.

No Python installation, Netlify account, subscription, or API key is needed on Windows. The game runs on your own computer; this repository is not an online game-hosting service.

## Requirements

- 64-bit Windows for the bundled runtime; a recent **Chrome or Edge with WebGPU and hardware acceleration** enabled.
- A capable GPU and sufficient memory. Tested locally on an RTX 3070 / 32 GB RAM computer; performance on other hardware is not guaranteed.
- About **25 GB free space** for automatic installation. Allow **45 GB** if keeping all manually downloaded ZIP files alongside the extracted game.
- Internet access for the initial roughly 21 GB download. The local game server serves the downloaded assets afterward.
- First world loading and shader preparation can take several minutes. Do not close the tab just because progress appears slow.

For lower-memory loading, try **http://localhost:8000/?low=1&fps=30**.

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

Double-click **`Verify-Game.cmd`** after installation. It compares every installed file with the published SHA-256 inventory. Verification reads about 21 GB and can take a few minutes. Release ZIP checksums are also listed in `SHA256SUMS.txt`.

The downloader does not overwrite existing files with different contents. If you have modified the game, download into a new empty folder instead.

## Other operating systems

Extract all release archives, install Python 3.11 or newer, and run `python3 serve_local.py --open` from the extracted folder. The bundled `runtime/python.exe` is Windows-only. Other operating systems have not been gameplay-tested for this package.

## Troubleshooting

- **Missing mirror / blank page:** finish downloading and extracting every release part. Run `Verify-Game.cmd`.
- **Address already in use:** another server is using port 8000. Use its existing tab, close that server, or run `runtime\python.exe serve_local.py --port 8001 --open`.
- **WebGPU unavailable:** update Chrome/Edge and your graphics driver; enable browser hardware acceleration.
- **Out of memory / tab crash:** close other tabs and applications, then try the lower-memory URL above.
- **Download failure:** rerun `Download-Game.cmd`. Completed, verified archives are remembered. Available disk space and network restrictions can affect downloading.
- **Windows security warning:** inspect the scripts and files before choosing to run them. Do not disable antivirus or system-wide security settings.

## Scope and provenance

This package contains only the original local game mirror, a local server, launch/download/verification scripts, and a minimal Python runtime. It does **not** contain hosting credentials, Netlify/Cloudflare configuration, personal saved games, Ollama, or the unfinished police-mode experiment. The double-nested source mirror folder is normalized to `mirror/playgta5.com` without changing its contents.

This package is not affiliated with or endorsed by Rockstar Games, Take-Two, or that project's authors.

Game names, artwork, audio, and other game assets remain the property of their respective rights holders. No ownership or redistribution license for those assets is claimed here. Availability is subject to rights-holder requests and GitHub's policies. The bundled Python runtime retains its license in `runtime/LICENSE.txt`.
