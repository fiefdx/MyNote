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
 * Writable state lives in <userData>/backend-home:
 *   configuration.yml   - generated config (MYNOTE_HOME env var tells the
 *                         backend to read it there, and to keep logs and the
 *                         pid file there too)
 *   data/               - MyNote DATA_PATH (db, index, storage, pictures...)
 */

const { app, BrowserWindow, Menu, dialog, shell } = require('electron');
const { spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

const IS_HEADLESS = process.env.MYNOTE_ELECTRON_HEADLESS === '1';
// Optional GUI smoke test: auto-quit N ms after the page finished loading.
const SMOKE_MS = parseInt(process.env.MYNOTE_SMOKE_MS || '0', 10);
const READY_TIMEOUT_MS = 90 * 1000;

let backend = null;
let backendPort = 0;
let mainWindow = null;
let quitting = false;

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

function writeBackendConfig(home, port) {
  const dataPath = path.join(home, 'data');
  fs.mkdirSync(dataPath, { recursive: true });
  const config = [
    'APP_DEBUG: false',
    'BIND_LOCAL: true',
    `DATA_PATH: ${JSON.stringify(dataPath)}`,
    'ENCRYPT: true',
    'LOG_LEVEL: INFO',
    'MAX_BUFFER_SIZE: 33554432',
    'NOTE_DESCRIPTION_LENGTH: 300',
    'PROCESS_NUM: 2',
    'SERVER_HOST: 127.0.0.1',
    `SERVER_PORT: ${port}`,
    'SERVER_SCHEME: http',
    'USB_MODE: false',
    'FUNCTIONS:',
    '  - rich',
    '  - note',
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
    if (!quitting) {
      dialog.showErrorBox('MyNote backend stopped',
        `The MyNote server process exited unexpectedly (code=${code}).\nSee logs in ${home}/logs`);
    }
    app.quit();
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
  const template = [
    { role: 'appMenu' },
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
  });

  app.on('window-all-closed', () => { app.quit(); });

  app.on('before-quit', (event) => {
    if (quitting) return;
    quitting = true;
    if (backend) {
      event.preventDefault();
      stopBackend().then(() => app.quit());
    }
  });
}
