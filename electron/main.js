'use strict';

/*
 * MyNote desktop shell.
 *
 * Starts the bundled MyNote backend (a PyInstaller onedir bundle of
 * app/MyNote.py, which carries its own CPython interpreter), waits until its
 * HTTP port is accepting connections on 127.0.0.1, then opens a BrowserWindow
 * pointed at the local server. The backend is shut down gracefully (SIGTERM)
 * when the window closes / the app quits.
 *
 * Writable state:
 *   <userData>/backend-home/            MYNOTE_HOME (config, logs, pid file)
 *   ~/MyNoteData/                       default DATA_PATH (notes, db, index)
 *     - override with the Preferences window (⌘,); choice persisted in
 *       <userData>/settings.json
 */

const { app, BrowserWindow, Menu, dialog, shell, ipcMain } = require('electron');
const { spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

const IS_HEADLESS = process.env.MYNOTE_ELECTRON_HEADLESS === '1';
// Optional GUI smoke test: auto-quit N ms after the page finished loading.
const SMOKE_MS = parseInt(process.env.MYNOTE_SMOKE_MS || '0', 10);
// Smoke test for the Preferences window (open it on start, log, auto-quit).
const OPEN_SETTINGS = process.env.MYNOTE_OPEN_SETTINGS === '1';
const READY_TIMEOUT_MS = 90 * 1000;

let backend = null;
let backendPort = 0;
let mainWindow = null;
let settingsWindow = null;
let quitting = false;        // graceful backend shutdown has been initiated
let backendStopped = false;  // backend is down; a quit may proceed
let restarting = false;

/* ---------- backend lifecycle ---------- */

function backendExecutable() {
  if (process.env.MYNOTE_BACKEND) return process.env.MYNOTE_BACKEND;
  const exe = process.platform === 'win32' ? 'MyNote.exe' : 'MyNote';
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', exe);
  }
  // dev mode: PyInstaller output at <repo>/dist/MyNote
  return path.join(__dirname, '..', 'dist', 'MyNote', exe);
}

function backendHome() {
  return path.join(app.getPath('userData'), 'backend-home');
}

/* ---------- user settings (persisted in <userData>/settings.json) ---------- */

function settingsFile() {
  return path.join(app.getPath('userData'), 'settings.json');
}

function loadSettings() {
  try {
    return JSON.parse(fs.readFileSync(settingsFile(), 'utf8'));
  } catch (e) {
    return {};
  }
}

function saveSettings(settings) {
  fs.writeFileSync(settingsFile(), JSON.stringify(settings, null, 2), 'utf8');
}

// Max upload (import package) size in MB. Tornado 6 caps request bodies at
// max_body_size, which defaults to max_buffer_size; too small a value makes
// large note-import uploads fail with "Content-Length too long".
const DEFAULT_MAX_BUFFER_MB = 512;

function maxBufferMb() {
  const mb = Number(loadSettings().maxBufferMb);
  return Number.isInteger(mb) && mb >= 16 && mb <= 4096 ? mb : DEFAULT_MAX_BUFFER_MB;
}

function defaultDataPath() {
  return path.join(app.getPath('home'), 'MyNoteData');
}

function currentDataPath() {
  const s = loadSettings();
  return s.dataPath || defaultDataPath();
}

function dirHasEntries(dir) {
  try {
    return fs.readdirSync(dir).length > 0;
  } catch (e) {
    return false;
  }
}

// Resolve the DATA_PATH and migrate old data when the default location
// changed (pre-v1.1 stored it inside Application Support/backend-home/data).
function ensureDataPath() {
  const target = currentDataPath();
  const legacy = path.join(backendHome(), 'data');
  if (!fs.existsSync(target) && target !== legacy && dirHasEntries(legacy)) {
    console.log(`[settings] migrating data ${legacy} -> ${target}`);
    fs.cpSync(legacy, target, { recursive: true });
  }
  fs.mkdirSync(target, { recursive: true });
  return target;
}

function writeBackendConfig(home, port) {
  const dataPath = ensureDataPath();
  const config = [
    'APP_DEBUG: false',
    'BIND_LOCAL: true',
    `DATA_PATH: ${JSON.stringify(dataPath)}`,
    'ENCRYPT: true',
    'LOG_LEVEL: INFO',
    'MAX_BUFFER_SIZE: ' + maxBufferMb() * 1024 * 1024, // also the Tornado 6 max request body size
    'NOTE_DESCRIPTION_LENGTH: 300',
    'PROCESS_NUM: 2',
    'SERVER_HOST: 127.0.0.1',
    `SERVER_PORT: ${port}`,
    'SERVER_SCHEME: http',
    'USB_MODE: false',
    'FUNCTIONS:',
    '  - rich',
    '',
  ].join('\n');
  fs.writeFileSync(path.join(home, 'configuration.yml'), config, 'utf8');
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

function waitForPort(port, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const sock = net.connect({ host: '127.0.0.1', port });
      sock.once('connect', () => { sock.end(); resolve(); });
      sock.once('error', () => {
        sock.destroy();
        if (Date.now() > deadline) {
          reject(new Error(`backend did not listen on 127.0.0.1:${port} within ${timeoutMs} ms`));
        } else if (backend && (backend.exitCode !== null || backend.killed)) {
          reject(new Error('backend process exited before it became ready'));
        } else {
          setTimeout(attempt, 400);
        }
      });
    };
    attempt();
  });
}

async function startBackend() {
  const exe = backendExecutable();
  if (!fs.existsSync(exe)) {
    throw new Error(
      `Backend not found: ${exe}\n` +
      'Build it first: npm run build:backend (from the electron/ directory)'
    );
  }
  const home = backendHome();
  fs.mkdirSync(home, { recursive: true });
  backendPort = await getFreePort();
  writeBackendConfig(home, backendPort);

  // Tornado 6 only accepts "--opt=value" (the separate-value form from
  // Tornado 5 raises "Option 'port' requires a value").
  const args = [`--port=${backendPort}`, '--log=MyNote.log'];
  const env = Object.assign({}, process.env, { MYNOTE_HOME: home });

  backend = spawn(exe, args, { env, stdio: ['ignore', 'pipe', 'pipe'] });
  backend.stdout.on('data', (d) => process.stdout.write(`[backend] ${d}`));
  backend.stderr.on('data', (d) => process.stderr.write(`[backend] ${d}`));
  backend.on('exit', (code, signal) => {
    console.log(`[backend] exited code=${code} signal=${signal}`);
    backend = null;
    if (!quitting && !restarting) {
      dialog.showErrorBox('MyNote backend stopped',
        `The MyNote server process exited unexpectedly (code=${code}).\nSee logs in ${home}/logs`);
    }
    if (!quitting && !restarting) app.quit();
  });

  await waitForPort(backendPort, READY_TIMEOUT_MS);
  console.log(`[backend] listening on http://127.0.0.1:${backendPort}`);
}

function stopBackend() {
  return new Promise((resolve) => {
    if (!backend) return resolve();
    const proc = backend;
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      resolve();
    };
    proc.once('exit', finish);
    try {
      // SIGINT/SIGTERM trigger the backend's graceful shutdown (common.sig_handler)
      proc.kill(process.platform === 'win32' ? undefined : 'SIGTERM');
    } catch (e) {
      console.error('failed to signal backend:', e.message);
    }
    setTimeout(() => {
      if (!done && proc.exitCode === null) {
        try { proc.kill('SIGKILL'); } catch (e) { /* ignore */ }
      }
      finish();
    }, 8000);
  });
}

// Restart the backend after a settings change (config is rewritten, port re-picked).
async function restartBackend() {
  restarting = true;
  try {
    await stopBackend();
    backend = null;
    await startBackend();
    if (mainWindow) mainWindow.loadURL(`http://127.0.0.1:${backendPort}/`);
  } catch (err) {
    console.error(err);
    dialog.showErrorBox('MyNote failed to restart', String(err.message || err));
  } finally {
    restarting = false;
  }
}

/* ---------- window ---------- */

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 800,
    minHeight: 600,
    title: 'MyNote',
    autoHideMenuBar: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(`http://127.0.0.1:${backendPort}/`);

  if (SMOKE_MS > 0) {
    mainWindow.webContents.once('did-finish-load', () => {
      console.log('MYNOTE_PAGE_LOADED url=' + mainWindow.webContents.getURL());
      setTimeout(() => app.quit(), SMOKE_MS);
    });
    mainWindow.webContents.once('did-fail-load', (e, code, desc) => {
      console.error('MYNOTE_PAGE_FAILED ' + code + ' ' + desc);
      app.quit();
    });
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

function buildMenu() {
  const appMenu = {
    label: app.name,
    submenu: [
      { role: 'about' },
      { type: 'separator' },
      { label: 'Preferences\u2026', accelerator: 'CmdOrCtrl+,', click: openSettings },
      { type: 'separator' },
      { role: 'services' },
      { type: 'separator' },
      { role: 'hide' },
      { role: 'hideOthers' },
      { role: 'unhide' },
      { type: 'separator' },
      { role: 'quit' },
    ],
  };
  const fileMenu = {
    label: 'File',
    submenu: [
      { label: 'Preferences\u2026', accelerator: 'CmdOrCtrl+,', click: openSettings },
      { type: 'separator' },
      { role: 'quit' },
    ],
  };
  const template = [
    process.platform === 'darwin' ? appMenu : fileMenu,
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    { role: 'editMenu' },
    { role: 'windowMenu' },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

/* ---------- preferences window ---------- */

function openSettings() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }
  settingsWindow = new BrowserWindow({
    width: 560,
    height: 300,
    title: 'MyNote Preferences',
    resizable: false,
    minimizable: false,
    parent: mainWindow || undefined,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  settingsWindow.loadFile(path.join(__dirname, 'settings.html'));
  settingsWindow.on('closed', () => { settingsWindow = null; });

  if (OPEN_SETTINGS) {
    settingsWindow.webContents.once('did-finish-load', () => {
      console.log('MYNOTE_SETTINGS_LOADED');
      setTimeout(() => app.quit(), SMOKE_MS || 1500);
    });
  }
}

ipcMain.handle('mynote:get-settings', () => {
  return {
    dataPath: currentDataPath(),
    defaultDataPath: defaultDataPath(),
    hasCustom: Boolean(loadSettings().dataPath),
    maxBufferMb: maxBufferMb(),
  };
});

ipcMain.handle('mynote:pick-data-path', async () => {
  const result = await dialog.showOpenDialog(settingsWindow || undefined, {
    title: 'Choose the MyNote data folder',
    defaultPath: currentDataPath(),
    properties: ['openDirectory', 'createDirectory'],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('mynote:save-settings', async (_event, values) => {
  const settings = loadSettings();
  if (values.useDefault) {
    delete settings.dataPath;
  } else if (values.dataPath && values.dataPath !== defaultDataPath()) {
    settings.dataPath = values.dataPath;
  } else {
    delete settings.dataPath;
  }
  const mb = Number(values.maxBufferMb);
  if (Number.isInteger(mb) && mb >= 16 && mb <= 4096) {
    settings.maxBufferMb = mb;
  } else {
    delete settings.maxBufferMb;
  }
  saveSettings(settings);
  await restartBackend();
  return { dataPath: currentDataPath(), maxBufferMb: maxBufferMb() };
});

/* ---------- app lifecycle ---------- */

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    try {
      await startBackend();
    } catch (err) {
      console.error(err);
      dialog.showErrorBox('MyNote failed to start', String(err.message || err));
      app.quit();
      return;
    }
    if (IS_HEADLESS) {
      // smoke-test mode: backend is up, print a marker and exit cleanly
      console.log('MYNOTE_BACKEND_READY port=' + backendPort);
      app.quit();
      return;
    }
    buildMenu();
    createWindow();
    if (OPEN_SETTINGS) openSettings();
  });

  app.on('window-all-closed', () => { app.quit(); });

  app.on('before-quit', (event) => {
    if (backendStopped) return;  // backend already down: allow the quit
    event.preventDefault();
    if (quitting) return;        // shutdown already running; wait for it
    quitting = true;
    stopBackend().then(() => {
      backendStopped = true;
      app.quit();
    });
  });
}
