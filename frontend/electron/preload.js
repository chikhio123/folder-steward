const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openInFolder: (path) => ipcRenderer.send('open-in-folder', path),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  onBackendError: (callback) => ipcRenderer.on('backend-error', (_event, message) => callback(message))
});

window.addEventListener('DOMContentLoaded', () => {
  console.log('Folder Steward Electron Preload Loaded');
});