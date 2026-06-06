/** Activity operations composition hook. */

import { useActivityStore } from '../stores/activityStore';
import { useTagStore } from '../stores/tagStore';
import type { Activity } from '@time-tracker/shared';

interface UseActivityResult {
  activities: Activity[];
  runningActivities: Activity[];
  pausedActivities: Activity[];
  endedActivities: Activity[];
  filteredActivities: Activity[];
  isLoading: boolean;
  error: string | null;

  startActivity: (id: string, parallel?: boolean) => Promise<void>;
  pauseActivity: (id: string) => Promise<void>;
  resumeActivity: (id: string) => Promise<void>;
  stopActivity: (id: string) => Promise<void>;
  deleteActivity: (id: string) => Promise<void>;
  refreshActivities: () => Promise<void>;
}

/**
 * Hook that provides activity operations with tag filtering support.
 * Combines activity and tag stores for filtered view.
 */
export function useActivity(): UseActivityResult {
  const {
    activities,
    runningActivities,
    pausedActivities,
    endedActivities,
    isLoading,
    error,
    fetchActivities,
    startActivity: start,
    pauseActivity: pause,
    resumeActivity: resume,
    stopActivity: stop,
    deleteActivity: remove,
  } = useActivityStore();

  const { selectedTagIds } = useTagStore();

  const filteredActivities = selectedTagIds.length > 0
    ? activities.filter((activity) =>
        activity.tags?.some((tag) => selectedTagIds.includes(tag.id))
      )
    : activities;

  return {
    activities,
    runningActivities,
    pausedActivities,
    endedActivities,
    filteredActivities,
    isLoading,
    error,
    startActivity: start,
    pauseActivity: pause,
    resumeActivity: resume,
    stopActivity: stop,
    deleteActivity: remove,
    refreshActivities: fetchActivities,
  };
}
