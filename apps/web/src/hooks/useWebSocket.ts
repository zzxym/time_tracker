/** WebSocket connection management hook. */

import { useEffect, useRef, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useSyncStore, type WSConnectionStatus } from '../stores/syncStore';
import { useActivityStore } from '../stores/activityStore';
import { WS_CONFIG } from '@time-tracker/shared';

interface UseWebSocketResult {
  connectionStatus: WSConnectionStatus;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for managing WebSocket connection with automatic reconnection,
 * heartbeat, and message handling.
 *
 * @returns WebSocket connection status and control functions.
 */
export function useWebSocket(): UseWebSocketResult {
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef<boolean>(true);

  const { accessToken, isAuthenticated } = useAuthStore();
  const {
    connectionStatus,
    setConnectionStatus,
    setLastMessageTime,
    reconnectAttempts,
    incrementReconnectAttempts,
    resetReconnectAttempts,
  } = useSyncStore();
  const { handleWSEvent } = useActivityStore();

  const getWsUrl = useCallback(() => {
    const wsBaseUrl =
      import.meta.env.VITE_WS_BASE_URL ||
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws`;
    const separator = wsBaseUrl.includes('?') ? '&' : '?';
    return `${wsBaseUrl}${separator}token=${accessToken}`;
  }, [accessToken]);

  const clearTimers = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!isAuthenticated || !accessToken) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const url = getWsUrl();

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setConnectionStatus('connected');
        resetReconnectAttempts();

        // Start heartbeat
        heartbeatRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, WS_CONFIG.HEARTBEAT_INTERVAL);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          setLastMessageTime(Date.now());

          if (data.type === 'pong') return;

          // Forward to activity store
          handleWSEvent(data);
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        setConnectionStatus('disconnected');
        clearTimers();

        // Attempt reconnection with exponential backoff
        const delay = Math.min(
          WS_CONFIG.RECONNECT_INITIAL_DELAY * Math.pow(WS_CONFIG.RECONNECT_MULTIPLIER, reconnectAttempts),
          WS_CONFIG.RECONNECT_MAX_DELAY
        );
        incrementReconnectAttempts();
        setConnectionStatus('reconnecting');

        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current && isAuthenticated) {
            connect();
          }
        }, delay);
      };

      ws.onerror = () => {
        // Error is handled by onclose
      };
    } catch {
      setConnectionStatus('disconnected');
    }
  }, [accessToken, isAuthenticated, getWsUrl, setConnectionStatus, setLastMessageTime, resetReconnectAttempts, incrementReconnectAttempts, clearTimers, handleWSEvent, reconnectAttempts]);

  const disconnect = useCallback(() => {
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, [clearTimers, setConnectionStatus]);

  // Auto-connect when authenticated
  useEffect(() => {
    mountedRef.current = true;
    if (isAuthenticated && accessToken) {
      connect();
    }
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [isAuthenticated, accessToken, connect, disconnect]);

  return { connectionStatus, connect, disconnect };
}
