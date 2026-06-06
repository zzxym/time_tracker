import { app, BrowserWindow, ipcMain, Tray, Menu, nativeImage } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;
let floatingWindow: BrowserWindow | null = null;
let tray: Tray | null = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'Time Tracker',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../web/dist/index.html'));
  }

  mainWindow.on('close', (event) => {
    if (floatingWindow && !floatingWindow.isDestroyed()) {
      floatingWindow.close();
    }
    mainWindow = null;
  });
}

function createFloatingWindow(): void {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.show();
    return;
  }

  floatingWindow = new BrowserWindow({
    width: 320,
    height: 120,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  floatingWindow.loadFile(path.join(__dirname, 'floating-window', 'floatingWindow.html'));

  // Make the floating window draggable
  floatingWindow.on('will-move', () => {
    // Default behavior is fine for dragging
  });

  floatingWindow.on('closed', () => {
    floatingWindow = null;
  });
}

function createTray(): void {
  const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
  const trayIcon = nativeImage.createFromPath(iconPath);
  tray = new Tray(trayIcon.resize({ width: 16, height: 16 }));

  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show Main Window', click: () => mainWindow?.show() },
    { label: 'Toggle Floating Window', click: () => createFloatingWindow() },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() },
  ]);

  tray.setToolTip('Time Tracker');
  tray.setContextMenu(contextMenu);
  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
      }
    }
  });
}

// IPC handlers
ipcMain.handle('toggle-floating-window', () => {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.close();
  } else {
    createFloatingWindow();
  }
});

ipcMain.handle('set-floating-opacity', (_event, opacity: number) => {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.setOpacity(Math.max(0.2, Math.min(1.0, opacity)));
  }
});

ipcMain.on('floating-window-drag', (_event, { deltaX, deltaY }: { deltaX: number; deltaY: number }) => {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    const [x, y] = floatingWindow.getPosition();
    floatingWindow.setPosition(x + deltaX, y + deltaY);
  }
});

ipcMain.on('update-floating-timer', (_event, data: { name: string; elapsed: string }) => {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.webContents.send('timer-update', data);
  }
});

// App lifecycle
app.whenReady().then(() => {
  createMainWindow();
  createTray();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (floatingWindow && !floatingWindow.isDestroyed()) {
    floatingWindow.close();
  }
});
