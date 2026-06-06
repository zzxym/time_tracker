/** Timer core logic service. */

import type { Activity, TimeSegment } from '@time-tracker/shared';
import { calculateElapsedSeconds, getCurrentSegmentStart } from '@time-tracker/shared';

/**
 * Get the total elapsed seconds for an activity, including the current running segment.
 */
export function getActivityElapsed(activity: Activity): number {
  if (activity.status !== 'RUNNING') {
    return activity.total_duration_seconds;
  }
  const segmentStart = activity.time_segments
    ? getCurrentSegmentStart(activity.time_segments)
    : null;
  return calculateElapsedSeconds(activity.total_duration_seconds, segmentStart);
}

/**
 * Get the current running time segment for an activity.
 */
export function getRunningSegment(activity: Activity): TimeSegment | null {
  if (!activity.time_segments || activity.status !== 'RUNNING') return null;
  return activity.time_segments.find((s) => s.end_time === null) || null;
}

/**
 * Calculate the duration of a specific time segment.
 */
export function getSegmentDuration(segment: TimeSegment): number {
  if (segment.end_time) {
    const start = new Date(segment.start_time).getTime();
    const end = new Date(segment.end_time).getTime();
    return Math.floor((end - start) / 1000);
  }
  const start = new Date(segment.start_time).getTime();
  const now = Date.now();
  return Math.floor((now - start) / 1000);
}
