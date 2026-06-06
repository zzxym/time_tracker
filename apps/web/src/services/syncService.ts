/** Data sync service for fallback polling and coordination. */

import type { WSConnectionStatus } from '../stores/syncStore';
import { useActivityStore } from '../stores/activityStore';

const POLL_INTERVAL = 5000; // 5 seconds
const MAX_POLL_INTERVAL = 30000; // 30 seconds

let pollTimer: ReturnType<typeof setInterval> | null = null;

/**
 * Start HTTP polling as a fallback when WebSocket is disconnected.
 */
export function startPolling(): void {
  if (pollTimer) return;

  pollTimer = setInterval(async () => {
    try {
      await useActivityStore.getState().fetchActivities();
    } catch {
      // Ignore polling errors
    }
  }, POLL_INTERVAL);
}

/**
 * Stop HTTP polling.
 */
export function stopPolling(): void {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

/**
 * Manage sync mode based on WebSocket connection status.
 * Automatically starts polling when WebSocket is disconnected.
 */
export function manageSyncMode(status: WSConnectionStatus): void {
  if (status === 'disconnected' || status === 'reconnecting') {
    startPolling();
  } else {
    stopPolling();
  }
}
