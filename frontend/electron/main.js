import { app, BrowserWindow, shell, ipcMain, dialog } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import isDev from 'electron-is-dev';
import { spawn } from 'child_process';
import http from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let backendProcess = null;
let pendingBackendError = null;

function notifyBackendError(message) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('backend-error', message);
  } else {
    pendingBackendError = message;
  }
}

function startBackend() {
  const backendDir = path.join(__dirname, '../../backend');

  const userDataPath = app.getPath('userData');
  const dbPath = path.join(userDataPath, 'folder_steward.db');

  const env = {
    ...process.env,
    FS_DATABASE_PATH: dbPath,
    PYTHONPATH: backendDir
  };

  console.log(`Starting backend. Database path: ${dbPath}`);

  if (isDev) {
    const pythonCommand = process.platform === 'win32' ? 'py' : 'python3';
    backendProcess = spawn(pythonCommand, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
      cwd: backendDir,
      env
    });
  } else {
    const exePath = path.join(process.resourcesPath, 'backend-bin', 'folder-steward-backend.exe');
    backendProcess = spawn(exePath, [], {
      env
    });
  }

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend Err] ${data.toString().trim()}`);
  });

  backendProcess.on('error', (err) => {
    console.error(`[Backend Spawn Error] Failed to start backend: ${err.message}`);
    notifyBackendError(err.message);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    if (code !== 0 && code !== null) {
      const errMsg = `FastAPI backend exited unexpectedly with code ${code}. Port 8000 might be in use.`;
      console.error(`[Backend Exit Error] ${errMsg}`);
      notifyBackendError(errMsg);
    }
  });
}

function waitUntilBackendReady() {
  return new Promise((resolve) => {
    let attempts = 0;
    const maxAttempts = 40; // 20 seconds
    const interval = setInterval(() => {
      attempts++;
      http.get('http://127.0.0.1:8000/health', (res) => {
        if (res.statusCode === 200) {
          clearInterval(interval);
          resolve(true);
        }
      }).on('error', () => {
        if (attempts >= maxAttempts) {
          clearInterval(interval);
          resolve(false);
        }
      });
    }, 500);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'Folder Steward'
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5174');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.webContents.once('did-finish-load', () => {
    if (pendingBackendError) {
      mainWindow.webContents.send('backend-error', pendingBackendError);
      pendingBackendError = null;
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  startBackend();
  const ready = await waitUntilBackendReady();
  createWindow();

  if (!ready) {
    notifyBackendError('核心服务启动超时，请检查 Python 环境、依赖或端口占用。');
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    console.log('Killing backend process...');
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', backendProcess.pid, '/f', '/t']);
    } else {
      backendProcess.kill();
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.on('open-in-folder', (event, filePath) => {
  if (!filePath || typeof filePath !== 'string') return;
  shell.showItemInFolder(filePath);
});

ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.canceled ? null : result.filePaths[0];
});