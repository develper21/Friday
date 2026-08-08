import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow;
let jeanMaxProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    titleBarStyle: 'hidden',
    transparent: true,
    backgroundColor: '#0B0F1A',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Load the app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for window controls
ipcMain.on('window-minimize', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.on('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('window-close', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});

// Jean Max voice assistant handlers
ipcMain.on('start-jean-max', () => {
  if (jeanMaxProcess) {
    console.log('Jean Max is already running');
    if (mainWindow) {
      mainWindow.webContents.send('jean-max-status', 'already-running');
    }
    return;
  }

  console.log('Starting Jean Max voice assistant...');
  try {
    jeanMaxProcess = spawn('python3', ['assistance/main.py'], {
      cwd: __dirname,
      stdio: 'pipe'
    });

    jeanMaxProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(`Jean Max: ${output}`);
      
      // Parse audio level from output if available
      const audioMatch = output.match(/audio[_\s]?level[:\s]+(\d+\.?\d*)/i);
      if (audioMatch) {
        if (mainWindow) {
          mainWindow.webContents.send('audio-level', parseFloat(audioMatch[1]));
        }
      }

      // Detect when Jean Max is speaking
      if (output.includes('[Jean Max]:') || output.includes('Speaking:')) {
        if (mainWindow) {
          mainWindow.webContents.send('jean-max-speaking', true);
        }
      }
    });

    jeanMaxProcess.stderr.on('data', (data) => {
      console.error(`Jean Max Error: ${data.toString()}`);
    });

    jeanMaxProcess.on('close', (code) => {
      console.log(`Jean Max process exited with code ${code}`);
      jeanMaxProcess = null;
      if (mainWindow) {
        mainWindow.webContents.send('jean-max-status', 'stopped');
        mainWindow.webContents.send('jean-max-speaking', false);
      }
    });

    if (mainWindow) {
      mainWindow.webContents.send('jean-max-status', 'started');
    }
  } catch (error) {
    console.error('Failed to start Jean Max:', error);
    if (mainWindow) {
      mainWindow.webContents.send('jean-max-status', 'error');
    }
  }
});

ipcMain.on('stop-jean-max', () => {
  if (jeanMaxProcess) {
    console.log('Stopping Jean Max...');
    jeanMaxProcess.kill();
    jeanMaxProcess = null;
    if (mainWindow) {
      mainWindow.webContents.send('jean-max-status', 'stopped');
      mainWindow.webContents.send('jean-max-speaking', false);
    }
  }
});

// Cleanup on app quit
app.on('before-quit', () => {
  if (jeanMaxProcess) {
    jeanMaxProcess.kill();
  }
});
