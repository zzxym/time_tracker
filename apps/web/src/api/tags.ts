/** Tags API functions. */

import apiClient from './client';
import type { APIResponse, Tag, CreateTagRequest, UpdateTagRequest } from '@time-tracker/shared';

/** List all tags for the current user. */
export async function listTags(): Promise<Tag[]> {
  const response = await apiClient.get<APIResponse<Tag[]>>('/tags');
  return response.data.data;
}

/** Create a new tag. */
export async function createTag(data: CreateTagRequest): Promise<Tag> {
  const response = await apiClient.post<APIResponse<Tag>>('/tags', data);
  return response.data.data;
}

/** Update a tag. */
export async function updateTag(tagId: string, data: UpdateTagRequest): Promise<Tag> {
  const response = await apiClient.put<APIResponse<Tag>>(`/tags/${tagId}`, data);
  return response.data.data;
}

/** Delete a tag. */
export async function deleteTag(tagId: string): Promise<void> {
  await apiClient.delete(`/tags/${tagId}`);
}
