import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window-minimize'),
  maximize: () => ipcRenderer.send('window-maximize'),
  close: () => ipcRenderer.send('window-close'),
  // Jean Max voice assistant communication
  startJeanMax: () => ipcRenderer.send('start-jean-max'),
  stopJeanMax: () => ipcRenderer.send('stop-jean-max'),
  onJeanMaxStatus: (callback) => ipcRenderer.on('jean-max-status', (_, status) => callback(status)),
  onAudioLevel: (callback) => ipcRenderer.on('audio-level', (_, level) => callback(level)),
  onJeanMaxSpeaking: (callback) => ipcRenderer.on('jean-max-speaking', (_, isSpeaking) => callback(isSpeaking)),
});
