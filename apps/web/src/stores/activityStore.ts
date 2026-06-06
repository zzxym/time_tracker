/** Activity state management with Zustand. */

import { create } from 'zustand';
import type { Activity } from '@time-tracker/shared';
import * as activitiesApi from '../api/activities';

interface ActivityState {
  activities: Activity[];
  runningActivities: Activity[];
  pausedActivities: Activity[];
  endedActivities: Activity[];
  isLoading: boolean;
  error: string | null;

  fetchActivities: () => Promise<void>;
  createActivity: (data: { name: string; color?: string; is_parallel?: boolean; tag_ids?: string[] }) => Promise<Activity>;
  startActivity: (id: string, parallel?: boolean) => Promise<void>;
  pauseActivity: (id: string) => Promise<void>;
  resumeActivity: (id: string) => Promise<void>;
  stopActivity: (id: string) => Promise<void>;
  deleteActivity: (id: string) => Promise<void>;
  updateActivity: (id: string, data: { name?: string; color?: string; is_parallel?: boolean; tag_ids?: string[] }) => Promise<void>;
  handleWSEvent: (event: { type: string; payload: Record<string, unknown> }) => void;
}

export const useActivityStore = create<ActivityState>()((set, get) => ({
  activities: [],
  runningActivities: [],
  pausedActivities: [],
  endedActivities: [],
  isLoading: false,
  error: null,

  fetchActivities: async () => {
    set({ isLoading: true, error: null });
    try {
      const result = await activitiesApi.listActivities({ page: 1, page_size: 100 });
      const activities = result.items;
      set({
        activities,
        runningActivities: activities.filter((a) => a.status === 'RUNNING'),
        pausedActivities: activities.filter((a) => a.status === 'PAUSED'),
        endedActivities: activities.filter((a) => a.status === 'ENDED'),
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false, error: String(error) });
    }
  },

  createActivity: async (data) => {
    const activity = await activitiesApi.createActivity(data);
    set((state) => ({
      activities: [activity, ...state.activities],
      pausedActivities: [activity, ...state.pausedActivities],
    }));
    return activity;
  },

  startActivity: async (id, parallel = false) => {
    try {
      const result = await activitiesApi.startActivity(id, parallel);

      // Update the started activity
      set((state) => {
        const updatedActivities = state.activities.map((a) =>
          a.id === id ? result.activity : a
        );

        // Handle auto-paused activities
        let activitiesWithPaused = updatedActivities;
        for (const paused of result.auto_paused) {
          activitiesWithPaused = activitiesWithPaused.map((a) =>
            a.id === paused.id ? paused : a
          );
        }

        return {
          activities: activitiesWithPaused,
          runningActivities: activitiesWithPaused.filter((a) => a.status === 'RUNNING'),
          pausedActivities: activitiesWithPaused.filter((a) => a.status === 'PAUSED'),
          endedActivities: activitiesWithPaused.filter((a) => a.status === 'ENDED'),
        };
      });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      throw new Error(err.response?.data?.message || '启动活动失败');
    }
  },

  pauseActivity: async (id) => {
    const activity = await activitiesApi.pauseActivity(id);
    set((state) => {
      const updated = state.activities.map((a) => (a.id === id ? activity : a));
      return {
        activities: updated,
        runningActivities: updated.filter((a) => a.status === 'RUNNING'),
        pausedActivities: updated.filter((a) => a.status === 'PAUSED'),
        endedActivities: updated.filter((a) => a.status === 'ENDED'),
      };
    });
  },

  resumeActivity: async (id) => {
    try {
      const activity = await activitiesApi.resumeActivity(id);
      set((state) => {
        const updated = state.activities.map((a) => (a.id === id ? activity : a));
        return {
          activities: updated,
          runningActivities: updated.filter((a) => a.status === 'RUNNING'),
          pausedActivities: updated.filter((a) => a.status === 'PAUSED'),
          endedActivities: updated.filter((a) => a.status === 'ENDED'),
        };
      });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      throw new Error(err.response?.data?.message || '恢复活动失败');
    }
  },

  stopActivity: async (id) => {
    const activity = await activitiesApi.stopActivity(id);
    set((state) => {
      const updated = state.activities.map((a) => (a.id === id ? activity : a));
      return {
        activities: updated,
        runningActivities: updated.filter((a) => a.status === 'RUNNING'),
        pausedActivities: updated.filter((a) => a.status === 'PAUSED'),
        endedActivities: updated.filter((a) => a.status === 'ENDED'),
      };
    });
  },

  deleteActivity: async (id) => {
    await activitiesApi.deleteActivity(id);
    set((state) => {
      const updated = state.activities.filter((a) => a.id !== id);
      return {
        activities: updated,
        runningActivities: updated.filter((a) => a.status === 'RUNNING'),
        pausedActivities: updated.filter((a) => a.status === 'PAUSED'),
        endedActivities: updated.filter((a) => a.status === 'ENDED'),
      };
    });
  },

  updateActivity: async (id, data) => {
    const activity = await activitiesApi.updateActivity(id, data);
    set((state) => {
      const updated = state.activities.map((a) => (a.id === id ? activity : a));
      return {
        activities: updated,
        runningActivities: updated.filter((a) => a.status === 'RUNNING'),
        pausedActivities: updated.filter((a) => a.status === 'PAUSED'),
        endedActivities: updated.filter((a) => a.status === 'ENDED'),
      };
    });
  },

  handleWSEvent: (event) => {
    const { type } = event;

    // Handle different event types from WebSocket
    if (
      type === 'activity_started' ||
      type === 'activity_paused' ||
      type === 'activity_resumed' ||
      type === 'activity_stopped' ||
      type === 'activity_updated'
    ) {
      // Refetch activities to get the latest state from server
      get().fetchActivities();
    }
  },
}));
