/**
 * JARVIS OS - Electron Main Process
 * =================================
 *
 * Desktop shell for JARVIS OS.
 * Responsibilities:
 * - Create and manage application window
 * - Start Python backend as subprocess
 * - Handle IPC between renderer and main
 * - System tray integration
 */

const { app, BrowserWindow, ipcMain, Tray, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const isDev = process.env.NODE_ENV === 'development';
const BACKEND_PORT = 8000;

let mainWindow = null;
let tray = null;
let backendProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    show: false,
    backgroundColor: '#0a0a0a',
  });

  // Load frontend
  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  if (isDev) {
    console.log('[JARVIS] Development mode — backend should be started manually');
    return;
  }

  const backendPath = path.join(__dirname, '..');
  backendProcess = spawn(
    process.platform === 'win32' ? 'python.exe' : 'python3',
    ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    {
      cwd: backendPath,
      stdio: 'pipe',
    }
  );

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] exited with code ${code}`);
  });
}

function createTray() {
  // Use a simple text tray if no icon available
  tray = new Tray(path.join(__dirname, '../docs/assets/jarvis_icon.png'));
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show JARVIS', click: () => mainWindow?.show() },
    { label: 'Quit', click: () => { app.quit(); } },
  ]);
  tray.setToolTip('JARVIS OS');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });
}

// App lifecycle
app.whenReady().then(() => {
  startBackend();
  createWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

// IPC handlers
ipcMain.handle('jarvis:get-version', () => {
  return { version: app.getVersion(), name: 'JARVIS OS' };
});

ipcMain.handle('jarvis:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.handle('jarvis:toggle-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});
