import { app, BrowserWindow, shell } from 'electron';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const consoleRoot = path.resolve(here, '..');
const port = Number(process.env.CONSOLE_PORT || 3040);
let serverProcess;
let window;

function startServer() {
  serverProcess = spawn(process.execPath, [path.join(consoleRoot, 'server', 'app.js')], {
    cwd: consoleRoot,
    env: { ...process.env, CONSOLE_PORT: String(port), CONSOLE_HOST: '127.0.0.1' },
    windowsHide: true,
    stdio: 'ignore',
  });
}

async function createWindow() {
  startServer();
  window = new BrowserWindow({ width: 1440, height: 900, minWidth: 960, minHeight: 640, autoHideMenuBar: true });
  window.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  await new Promise((resolve) => setTimeout(resolve, 500));
  await window.loadURL(`http://127.0.0.1:${port}`);
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => app.quit());
app.on('will-quit', () => serverProcess?.kill());
