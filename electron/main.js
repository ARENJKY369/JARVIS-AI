/**
 * JARVIS OS - Electron Main Process (Enhanced)
 * ==============================================
 *
 * Desktop shell for JARVIS OS with full system integration.
 * Responsibilities:
 * - Create and manage application window
 * - Start Python backend as subprocess
 * - Handle IPC between renderer and main
 * - System tray integration
 * - Global hotkey (Ctrl+J) for quick access
 * - Always-on overlay HUD window
 * - Boot with OS configuration
 */

const { app, BrowserWindow, ipcMain, Tray, Menu, globalShortcut, screen } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const isDev = process.env.NODE_ENV === 'development';
const BACKEND_PORT = 8000;

let mainWindow = null;
let overlayWindow = null;
let tray = null;
let backendProcess = null;

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: Math.min(1400, width - 100),
    height: Math.min(900, height - 100),
    minWidth: 900,
    minHeight: 600,
    titleBarStyle: 'hiddenInset',
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
    show: false,
    backgroundColor: '#05080F',
    icon: path.join(__dirname, '../docs/assets/jarvis_icon.png'),
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

  // Minimize to tray instead of closing
  mainWindow.on('close', (event) => {
    if (!app.isQuiting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });
}

function createOverlay() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  overlayWindow = new BrowserWindow({
    width: 400,
    height: 600,
    x: width - 420,
    y: 20,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    movable: true,
    show: false,
    backgroundColor: '#00000000',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    hasShadow: false,
  });

  overlayWindow.loadFile(path.join(__dirname, 'overlay.html'));
  overlayWindow.setAlwaysOnTop(true, 'floating');
  overlayWindow.setVisibleOnAllWorkspaces(true);

  overlayWindow.on('closed', () => {
    overlayWindow = null;
  });
}

function toggleOverlay() {
  if (overlayWindow) {
    if (overlayWindow.isVisible()) {
      overlayWindow.hide();
    } else {
      overlayWindow.show();
    }
  }
}

function createTray() {
  const iconPath = path.join(__dirname, '../docs/assets/jarvis_icon.png');
  tray = new Tray(iconPath);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show JARVIS',
      click: () => mainWindow?.show(),
    },
    {
      label: 'Toggle HUD',
      click: () => toggleOverlay(),
    },
    { type: 'separator' },
    {
      label: 'Voice Console',
      click: () => {
        mainWindow?.show();
        mainWindow?.webContents.send('navigate', '/console');
      },
    },
    {
      label: 'Iron Man HUD',
      click: () => {
        mainWindow?.show();
        mainWindow?.webContents.send('navigate', '/console_hud');
      },
    },
    { type: 'separator' },
    {
      label: 'Start with OS',
      type: 'checkbox',
      checked: isStartupEnabled(),
      click: (menuItem) => setStartup(menuItem.checked),
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuiting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('JARVIS OS — At your service, sir.');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    if (mainWindow) {
      mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
    }
  });

  tray.on('double-click', () => {
    mainWindow?.show();
  });
}

function registerGlobalShortcuts() {
  // Ctrl+J / Cmd+J to toggle JARVIS
  globalShortcut.register('CommandOrControl+J', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    }
  });

  // Ctrl+Shift+J / Cmd+Shift+J to toggle overlay
  globalShortcut.register('CommandOrControl+Shift+J', () => {
    toggleOverlay();
  });

  // Ctrl+Alt+J / Cmd+Alt+J for quick voice command
  globalShortcut.register('CommandOrControl+Alt+J', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
      mainWindow.webContents.send('trigger-voice');
    }
  });
}

function unregisterGlobalShortcuts() {
  globalShortcut.unregisterAll();
}

function isStartupEnabled() {
  const platform = process.platform;
  if (platform === 'linux') {
    const autostartFile = path.join(
      require('os').homedir(),
      '.config', 'autostart', 'jarvis-os.desktop'
    );
    return fs.existsSync(autostartFile);
  } else if (platform === 'darwin') {
    const plistFile = path.join(
      require('os').homedir(),
      'Library', 'LaunchAgents', 'dev.jarvis-os.plist'
    );
    return fs.existsSync(plistFile);
  } else if (platform === 'win32') {
    // Check registry
    try {
      const { execSync } = require('child_process');
      const result = execSync(
        'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "JARVIS OS"',
        { encoding: 'utf8' }
      );
      return result.includes('JARVIS OS');
    } catch {
      return false;
    }
  }
  return false;
}

function setStartup(enable) {
  const platform = process.platform;
  const appPath = app.getAppPath();
  const scriptPath = path.join(appPath, 'scripts', 'start_jarvis.sh');

  if (platform === 'linux') {
    const autostartDir = path.join(require('os').homedir(), '.config', 'autostart');
    const desktopFile = path.join(autostartDir, 'jarvis-os.desktop');

    if (enable) {
      fs.mkdirSync(autostartDir, { recursive: true });
      const content = `[Desktop Entry]
Type=Application
Name=JARVIS OS
Comment=JARVIS AI Desktop Assistant
Exec=${scriptPath}
Icon=${path.join(appPath, 'docs', 'assets', 'jarvis_icon.png')}
Terminal=false
StartupNotify=true
`;
      fs.writeFileSync(desktopFile, content);
      fs.chmodSync(desktopFile, 0o755);
    } else {
      if (fs.existsSync(desktopFile)) {
        fs.unlinkSync(desktopFile);
      }
    }
  } else if (platform === 'darwin') {
    const plistDir = path.join(require('os').homedir(), 'Library', 'LaunchAgents');
    const plistFile = path.join(plistDir, 'dev.jarvis-os.plist');

    if (enable) {
      fs.mkdirSync(plistDir, { recursive: true });
      const content = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>dev.jarvis-os</string>
    <key>ProgramArguments</key>
    <array>
        <string>${scriptPath}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
`;
      fs.writeFileSync(plistFile, content);
    } else {
      if (fs.existsSync(plistFile)) {
        fs.unlinkSync(plistFile);
      }
    }
  } else if (platform === 'win32') {
    const { execSync } = require('child_process');
    if (enable) {
      execSync(
        `reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "JARVIS OS" /t REG_SZ /d "${scriptPath}" /f`
      );
    } else {
      try {
        execSync(
          `reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "JARVIS OS" /f`
        );
      } catch {
        // Value may not exist
      }
    }
  }
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

// App lifecycle
app.whenReady().then(() => {
  startBackend();
  createWindow();
  createOverlay();
  createTray();
  registerGlobalShortcuts();

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
  unregisterGlobalShortcuts();
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

ipcMain.handle('jarvis:hide', () => {
  mainWindow?.hide();
});

ipcMain.handle('jarvis:show', () => {
  mainWindow?.show();
  mainWindow?.focus();
});

ipcMain.handle('jarvis:toggle-overlay', () => {
  toggleOverlay();
});

ipcMain.handle('jarvis:get-startup', () => {
  return { enabled: isStartupEnabled() };
});

ipcMain.handle('jarvis:set-startup', (event, enable) => {
  setStartup(enable);
  return { success: true, enabled: isStartupEnabled() };
});

ipcMain.handle('jarvis:quit', () => {
  app.isQuiting = true;
  app.quit();
});
