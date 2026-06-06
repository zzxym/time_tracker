import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  toggleFloatingWindow: () => ipcRenderer.invoke('toggle-floating-window'),
  setFloatingOpacity: (opacity: number) => ipcRenderer.invoke('set-floating-opacity', opacity),
  onTimerUpdate: (callback: (data: { name: string; elapsed: string }) => void) => {
    ipcRenderer.on('timer-update', (_event, data) => callback(data));
  },
  startDragging: (deltaX: number, deltaY: number) => {
    ipcRenderer.send('floating-window-drag', { deltaX, deltaY });
  },
});

export interface ElectronAPI {
  toggleFloatingWindow: () => Promise<void>;
  setFloatingOpacity: (opacity: number) => Promise<void>;
  onTimerUpdate: (callback: (data: { name: string; elapsed: string }) => void) => void;
  startDragging: (deltaX: number, deltaY: number) => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
