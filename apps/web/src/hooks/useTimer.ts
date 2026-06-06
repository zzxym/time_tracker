/** Timer hook for second-by-second elapsed time display. */

import { useState, useEffect, useCallback, useRef } from 'react';
import { TIMER_REFRESH_INTERVAL } from '@time-tracker/shared';
import { calculateElapsedSeconds, getCurrentSegmentStart, formatDuration } from '@time-tracker/shared';
import type { Activity, TimeSegment } from '@time-tracker/shared';

interface UseTimerResult {
  /** Formatted elapsed time string (HH:MM:SS). */
  display: string;
  /** Total elapsed seconds. */
  elapsedSeconds: number;
  /** Whether the timer is currently running. */
  isRunning: boolean;
}

/**
 * Hook that provides a real-time timer display for an activity.
 * Updates every second when the activity is running.
 *
 * @param activity - The activity to track time for.
 * @returns Timer display info including formatted string and raw seconds.
 */
export function useTimer(activity: Activity | null): UseTimerResult {
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isRunning = activity?.status === 'RUNNING';

  const updateTimer = useCallback(() => {
    if (!activity) return;

    if (activity.status === 'RUNNING') {
      const segmentStart = activity.time_segments
        ? getCurrentSegmentStart(activity.time_segments)
        : null;
      const elapsed = calculateElapsedSeconds(
        activity.total_duration_seconds,
        segmentStart
      );
      setElapsedSeconds(elapsed);
    } else {
      setElapsedSeconds(activity.total_duration_seconds);
    }
  }, [activity]);

  useEffect(() => {
    // Initial update
    updateTimer();

    if (isRunning) {
      // Start interval for running activities
      intervalRef.current = setInterval(updateTimer, TIMER_REFRESH_INTERVAL);
    } else {
      // Clear interval for non-running activities
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRunning, updateTimer]);

  const display = formatDuration(elapsedSeconds);

  return { display, elapsedSeconds, isRunning };
}
