'use strict';

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('mynoteSettings', {
  get: () => ipcRenderer.invoke('mynote:get-settings'),
  pick: () => ipcRenderer.invoke('mynote:pick-data-path'),
  save: (values) => ipcRenderer.invoke('mynote:save-settings', values),
});
