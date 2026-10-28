# MyNote Desktop (Electron shell)

A standalone desktop application: an Electron window wrapping the existing
MyNote Tornado web backend. The Python backend is frozen with **PyInstaller**
(`onedir` bundle, see `../MyNoteElectron.spec`) and ships with its **own
CPython interpreter** — end users need no Python installed.

## How it works

- `build-backend.sh` creates `.venv-electron`, installs
  `../requires/requirements.txt` + PyInstaller, and builds `../dist/MyNote/`
  (contains the `MyNote` executable + `_internal/` with the interpreter and
  all dependencies, static/templates/translations, jieba dicts, whoosh, lxml…).
- `main.js` (Electron main process):
  1. picks a free port on `127.0.0.1`,
  2. writes a generated `configuration.yml` into
     `<userData>/backend-home/` (`~/Library/Application Support/MyNote/` on
     macOS) and exports it via the `MYNOTE_HOME` env var,
  3. spawns the bundled backend (`--port=NNNN --log=MyNote.log`),
  4. waits for the port, then opens a `BrowserWindow` at `http://127.0.0.1:PORT/`,
  5. sends `SIGTERM` on quit — the backend shuts down gracefully
     (`utils/common.shutdown` closes DBs, index, worker processes).
- electron-builder copies `../dist/MyNote` into the app bundle as
  `Contents/Resources/backend`.

## Data location

- Default data folder (notes, SQLite DBs, whoosh index, pictures, uploads):
  **`~/MyNoteData`** (home directory).
- Change it via **MyNote ▸ Preferences (⌘,)**: pick any folder; the choice is
  saved in `<userData>/settings.json` and the backend restarts automatically.
  “Use default” resets back to `~/MyNoteData`.
- Logs, generated `configuration.yml` and the pid file stay in
  `<userData>/backend-home/` (`~/Library/Application Support/MyNote/` on macOS).
- Data found in the old pre-1.1 location
  (`<userData>/backend-home/data`) is copied to the default folder once,
  automatically, on first launch.

All user data (SQLite DBs, whoosh index, pictures, uploads, logs) lives under
`<userData>/backend-home/data` — the app bundle stays read-only friendly.

## Commands (run inside `electron/`)

```bash
npm install              # electron + electron-builder
npm run build:backend    # PyInstaller bundle -> ../dist/MyNote
npm start                # run the desktop app (dev mode, uses ../dist/MyNote)
npm run dist             # build backend + package installer
                         # (macOS: dmg, Windows: nsis, Linux: AppImage)
```

Smoke tests (no manual interaction):

```bash
MYNOTE_ELECTRON_HEADLESS=1 npm start   # start backend, verify port, quit
MYNOTE_SMOKE_MS=4000 npm start         # open window, quit 4s after page load
MYNOTE_OPEN_SETTINGS=1 npm start       # also open the Preferences window
```

## Notes / gotchas

- **Tornado 6 only accepts `--opt=value`** on the command line; the older
  `--port 8008` form raises `Option 'port' requires a value`.
- **`multiprocessing.freeze_support()` must be the very first thing** the
  entry script does (before imports): `utils/processer.py` used to create
  `multiprocessing.Queue`s at import time, and frozen helper processes
  (resource tracker / spawn workers) re-execute the entry script — queues
  created during those re-execs spawn further trackers (runaway explosion).
  `app/MyNote.py` now has a prelude that calls `freeze_support()` before any
  heavy import, and the queues are created lazily in `ManagerClient`.
- The shell always forces `SERVER_SCHEME: http` and `BIND_LOCAL: true`
  (localhost only, no self-signed TLS inside Electron).
- Build the backend on the same OS/arch you package for (PyInstaller does not
  cross-compile).
- `MyNoteGUI.py` (the old wxPython tray app) is **not** bundled; Electron
  replaces it. Its top-level process creation is still not `spawn`-safe.
