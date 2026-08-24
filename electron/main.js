const { app, BrowserWindow } = require('electron')
const path = require('path')
const fs = require('fs')
const http = require('http')
const { spawn } = require('child_process')

const BACKEND_HOST = '127.0.0.1'
const BACKEND_PORT = 8000
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`
const HEALTH_URL = `${BACKEND_URL}/health`
const HEALTH_TIMEOUT_MS = 60000
const HEALTH_POLL_INTERVAL_MS = 400

let splashWindow = null
let mainWindow = null
let backendProcess = null

function resolveBackendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend')
  }
  return path.join(__dirname, '..', 'backend')
}

function resolveStaticDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'frontend', 'dist')
  }
  return path.join(__dirname, '..', 'frontend', 'dist')
}

function resolvePythonExecutable(backendDir) {
  // Windows desktop build: install.sh creates a venv inside backend/.venv
  // using the target machine's own Python, so it always matches the OS.
  const venvPython = process.platform === 'win32'
    ? path.join(backendDir, '.venv', 'Scripts', 'python.exe')
    : path.join(backendDir, '.venv', 'bin', 'python')

  if (fs.existsSync(venvPython)) {
    return venvPython
  }

  // Dev fallback: rely on whatever Python is on PATH.
  return process.platform === 'win32' ? 'python' : 'python3'
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 420,
    frame: false,
    transparent: true,
    resizable: false,
    movable: false,
    show: false,
    skipTaskbar: true,
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  })

  splashWindow.loadFile(path.join(__dirname, 'splash.html'))
  splashWindow.once('ready-to-show', () => {
    splashWindow.show()
  })
  splashWindow.on('closed', () => {
    splashWindow = null
  })
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    show: false,
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  })

  mainWindow.loadURL(BACKEND_URL)
  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      splashWindow.close()
    }
    mainWindow.show()
  })
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function runBootstrap(pythonExe, backendDir, env) {
  return new Promise((resolve, reject) => {
    const child = spawn(pythonExe, ['scripts/bootstrap_desktop.py'], {
      cwd: backendDir,
      env,
    })
    child.stdout.on('data', (chunk) => process.stdout.write(`[bootstrap] ${chunk}`))
    child.stderr.on('data', (chunk) => process.stderr.write(`[bootstrap] ${chunk}`))
    child.on('error', reject)
    child.on('exit', (code) => {
      if (code === 0) {
        resolve()
      } else {
        reject(new Error(`bootstrap_desktop.py exited with code ${code}`))
      }
    })
  })
}

function startBackendServer(pythonExe, backendDir, env) {
  backendProcess = spawn(
    pythonExe,
    ['-m', 'uvicorn', 'app.main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)],
    { cwd: backendDir, env },
  )
  backendProcess.stdout.on('data', (chunk) => process.stdout.write(`[backend] ${chunk}`))
  backendProcess.stderr.on('data', (chunk) => process.stderr.write(`[backend] ${chunk}`))
  backendProcess.on('exit', (code) => {
    backendProcess = null
    if (code !== 0 && code !== null && mainWindow === null && splashWindow) {
      // Backend died before the dashboard ever loaded: nothing to show.
      app.quit()
    }
  })
}

function waitForHealth(deadline) {
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(HEALTH_URL, (res) => {
        res.resume()
        if (res.statusCode === 200) {
          resolve()
        } else {
          retry()
        }
      })
      req.on('error', retry)
    }
    const retry = () => {
      if (Date.now() > deadline) {
        reject(new Error('Timed out waiting for backend health check'))
        return
      }
      setTimeout(attempt, HEALTH_POLL_INTERVAL_MS)
    }
    attempt()
  })
}

async function boot() {
  createSplashWindow()

  const backendDir = resolveBackendDir()
  const staticDir = resolveStaticDir()
  const pythonExe = resolvePythonExecutable(backendDir)

  const env = {
    ...process.env,
    STATIC_DIR: staticDir,
    FRONTEND_ORIGIN: BACKEND_URL,
    DATABASE_URL: `sqlite:///${path.join(backendDir, 'elite.db').replace(/\\/g, '/')}`,
    CATALOG_XLSX_PATH: path.join(backendDir, 'data', 'raw', 'PRECIOS_PRODUCTOS_PAPELERIA.xlsx'),
    PERSIST_TRANSACTIONS_CSV: path.join(backendDir, 'data', 'raw', '2026-2.csv'),
    PYTHONUNBUFFERED: '1',
  }

  try {
    await runBootstrap(pythonExe, backendDir, env)
    startBackendServer(pythonExe, backendDir, env)
    await waitForHealth(Date.now() + HEALTH_TIMEOUT_MS)
    createMainWindow()
  } catch (err) {
    console.error('Failed to start Elite Intel:', err)
    app.quit()
  }
}

app.whenReady().then(boot)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill()
    backendProcess = null
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    boot()
  }
})
