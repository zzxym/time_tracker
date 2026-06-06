/** WebSocket sync state management with Zustand. */

import { create } from 'zustand';
import { WS_CONFIG } from '@time-tracker/shared';

export type WSConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

interface SyncState {
  connectionStatus: WSConnectionStatus;
  lastMessageTime: number | null;
  reconnectAttempts: number;

  setConnectionStatus: (status: WSConnectionStatus) => void;
  setLastMessageTime: (time: number) => void;
  incrementReconnectAttempts: () => void;
  resetReconnectAttempts: () => void;
}

export const useSyncStore = create<SyncState>()((set) => ({
  connectionStatus: 'disconnected',
  lastMessageTime: null,
  reconnectAttempts: 0,

  setConnectionStatus: (status) => set({ connectionStatus: status }),
  setLastMessageTime: (time) => set({ lastMessageTime: time }),
  incrementReconnectAttempts: () =>
    set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 })),
  resetReconnectAttempts: () => set({ reconnectAttempts: 0 }),
}));
