// Time formatting and duration calculation utilities
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import duration from 'dayjs/plugin/duration';

dayjs.extend(utc);
dayjs.extend(duration);

/**
 * Format seconds into HH:MM:SS display string.
 * @param totalSeconds - Total seconds to format
 * @returns Formatted string like "01:23:45"
 */
export function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

/**
 * Format seconds into human-readable string.
 * @param totalSeconds - Total seconds to format
 * @returns Formatted string like "1h 23m 45s"
 */
export function formatDurationHuman(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
  return parts.join(' ');
}

/**
 * Calculate elapsed seconds for a running activity.
 * For a running activity, actual duration = total_duration_seconds + current segment elapsed.
 * @param totalDurationSeconds - The stored cumulative duration (excluding current running segment)
 * @param currentSegmentStartTime - ISO string of the current running segment start time (null if not running)
 * @returns Total elapsed seconds
 */
export function calculateElapsedSeconds(
  totalDurationSeconds: number,
  currentSegmentStartTime: string | null
): number {
  if (!currentSegmentStartTime) {
    return totalDurationSeconds;
  }
  const now = dayjs.utc();
  const segmentStart = dayjs.utc(currentSegmentStartTime);
  const segmentElapsed = now.diff(segmentStart, 'second');
  return totalDurationSeconds + Math.max(0, segmentElapsed);
}

/**
 * Get the start time of the current running time segment.
 * @param segments - Array of time segments
 * @returns The start_time of the open segment, or null
 */
export function getCurrentSegmentStart(segments: Array<{ start_time: string; end_time: string | null }>): string | null {
  const openSegment = segments.find((s) => s.end_time === null);
  return openSegment ? openSegment.start_time : null;
}

/**
 * Format an ISO date string to local display format.
 * @param isoString - ISO 8601 date string
 * @param format - dayjs format string (default: 'YYYY-MM-DD HH:mm')
 * @returns Formatted date string
 */
export function formatDateTime(isoString: string, format: string = 'YYYY-MM-DD HH:mm'): string {
  return dayjs(isoString).format(format);
}

/**
 * Format an ISO date string to date only.
 * @param isoString - ISO 8601 date string
 * @returns Formatted date string like "2024-01-15"
 */
export function formatDate(isoString: string): string {
  return dayjs(isoString).format('YYYY-MM-DD');
}

/**
 * Get the start of day for a given date.
 * @param date - ISO date string or Dayjs object
 * @returns Dayjs object at start of day (UTC)
 */
export function startOfDay(date: string | dayjs.Dayjs): dayjs.Dayjs {
  const d = typeof date === 'string' ? dayjs.utc(date) : date;
  return d.startOf('day');
}

/**
 * Get the end of day for a given date.
 * @param date - ISO date string or Dayjs object
 * @returns Dayjs object at end of day (UTC)
 */
export function endOfDay(date: string | dayjs.Dayjs): dayjs.Dayjs {
  const d = typeof date === 'string' ? dayjs.utc(date) : date;
  return d.endOf('day');
}

/**
 * Get the start of week (Monday) for a given date.
 * @param date - ISO date string or Dayjs object
 * @returns Dayjs object at start of week (UTC)
 */
export function startOfWeek(date: string | dayjs.Dayjs): dayjs.Dayjs {
  const d = typeof date === 'string' ? dayjs.utc(date) : date;
  return d.startOf('week').add(1, 'day'); // Monday
}

/**
 * Get the start of month for a given date.
 * @param date - ISO date string or Dayjs object
 * @returns Dayjs object at start of month (UTC)
 */
export function startOfMonth(date: string | dayjs.Dayjs): dayjs.Dayjs {
  const d = typeof date === 'string' ? dayjs.utc(date) : date;
  return d.startOf('month');
}
