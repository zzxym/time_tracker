// Constants for the time tracker application

/** Maximum number of parallel running activities */
export const MAX_PARALLEL = 2;

/** Activity status enum values */
export const ACTIVITY_STATUS = {
  RUNNING: 'RUNNING',
  PAUSED: 'PAUSED',
  ENDED: 'ENDED',
} as const;

/** API error codes */
export const API_ERROR_CODES = {
  SUCCESS: 0,
  UNAUTHORIZED: 40101,
  TOKEN_EXPIRED: 40102,
  PARALLEL_CONFLICT: 40901,
  NOT_FOUND: 40401,
  VALIDATION_ERROR: 40001,
  SERVER_ERROR: 50001,
} as const;

/** WebSocket message types */
export const WS_MESSAGE_TYPES = {
  ACTIVITY_STARTED: 'activity_started',
  ACTIVITY_PAUSED: 'activity_paused',
  ACTIVITY_RESUMED: 'activity_resumed',
  ACTIVITY_STOPPED: 'activity_stopped',
  ACTIVITY_UPDATED: 'activity_updated',
  TAG_CREATED: 'tag_created',
  TAG_UPDATED: 'tag_updated',
  TAG_DELETED: 'tag_deleted',
  PING: 'ping',
  PONG: 'pong',
} as const;

/** WebSocket configuration */
export const WS_CONFIG = {
  /** Heartbeat interval in milliseconds */
  HEARTBEAT_INTERVAL: 30000,
  /** Initial reconnect delay in milliseconds */
  RECONNECT_INITIAL_DELAY: 1000,
  /** Maximum reconnect delay in milliseconds */
  RECONNECT_MAX_DELAY: 30000,
  /** Reconnect backoff multiplier */
  RECONNECT_MULTIPLIER: 2,
} as const;

/** Token expiration */
export const TOKEN_EXPIRY = {
  ACCESS_TOKEN_MINUTES: 15,
  REFRESH_TOKEN_DAYS: 7,
} as const;

/** Default page size for pagination */
export const DEFAULT_PAGE_SIZE = 20;

/** Default activity colors */
export const DEFAULT_COLORS = [
  '#4CAF50', '#2196F3', '#FF9800', '#9C27B0',
  '#F44336', '#00BCD4', '#795548', '#607D8B',
  '#E91E63', '#3F51B5', '#CDDC39', '#FF5722',
] as const;

/** Timer refresh interval in milliseconds */
export const TIMER_REFRESH_INTERVAL = 1000;
