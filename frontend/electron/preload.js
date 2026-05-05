const { ipcRenderer } = require('electron');

window.electronAPI = {
  openInFolder: (path) => ipcRenderer.send('open-in-folder', path)
};

window.addEventListener('DOMContentLoaded', () => {
  console.log('Folder Steward Electron Preload Loaded');
});