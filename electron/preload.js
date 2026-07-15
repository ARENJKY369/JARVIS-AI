/**
 * JARVIS OS - Electron Preload Script
 * ===================================
 *
 * Secure bridge between renderer process and main process.
 * Exposes only whitelisted APIs to the frontend.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvisAPI', {
  getVersion: () => ipcRenderer.invoke('jarvis:get-version'),
  minimize: () => ipcRenderer.invoke('jarvis:minimize'),
  toggleMaximize: () => ipcRenderer.invoke('jarvis:toggle-maximize'),
  platform: process.platform,
});
