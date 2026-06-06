/** Activities API functions. */

import apiClient from './client';
import type {
  Activity, CreateActivityRequest, UpdateActivityRequest,
  ActivityListResponse, StartActivityRequest,
} from '@time-tracker/shared';

/** List activities with optional filters. */
export async function listActivities(params?: {
  status?: string;
  tag_id?: string;
  page?: number;
  page_size?: number;
}): Promise<ActivityListResponse> {
  const response = await apiClient.get<ActivityListResponse>('/activities', { params });
  return response.data;
}

/** Get a single activity by ID. */
export async function getActivity(activityId: string): Promise<Activity> {
  const response = await apiClient.get<Activity>(`/activities/${activityId}`);
  return response.data;
}

/** Create a new activity. */
export async function createActivity(data: CreateActivityRequest): Promise<Activity> {
  const response = await apiClient.post<Activity>('/activities', data);
  return response.data;
}

/** Start an activity (with optional parallel mode). */
export async function startActivity(
  activityId: string,
  parallel: boolean = false
): Promise<{ activity: Activity; auto_paused: Activity[] }> {
  const data: StartActivityRequest = { parallel };
  const response = await apiClient.post<{ activity: Activity; auto_paused: Activity[] }>(
    `/activities/${activityId}/start`,
    data
  );
  return response.data;
}

/** Pause a running activity. */
export async function pauseActivity(activityId: string): Promise<Activity> {
  const response = await apiClient.post<Activity>(`/activities/${activityId}/pause`);
  return response.data;
}

/** Resume a paused activity. */
export async function resumeActivity(activityId: string): Promise<Activity> {
  const response = await apiClient.post<Activity>(`/activities/${activityId}/resume`);
  return response.data;
}

/** Stop (end) an activity. */
export async function stopActivity(activityId: string): Promise<Activity> {
  const response = await apiClient.post<Activity>(`/activities/${activityId}/stop`);
  return response.data;
}

/** Update activity properties. */
export async function updateActivity(
  activityId: string,
  data: UpdateActivityRequest
): Promise<Activity> {
  const response = await apiClient.put<Activity>(`/activities/${activityId}`, data);
  return response.data;
}

/** Delete an activity. */
export async function deleteActivity(activityId: string): Promise<void> {
  await apiClient.delete(`/activities/${activityId}`);
}
