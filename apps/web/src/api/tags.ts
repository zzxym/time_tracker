/** Tags API functions. */

import apiClient from './client';
import type { Tag, CreateTagRequest, UpdateTagRequest } from '@time-tracker/shared';

/** List all tags for the current user. */
export async function listTags(): Promise<Tag[]> {
  const response = await apiClient.get<Tag[]>('/tags');
  return response.data;
}

/** Create a new tag. */
export async function createTag(data: CreateTagRequest): Promise<Tag> {
  const response = await apiClient.post<Tag>('/tags', data);
  return response.data;
}

/** Update a tag. */
export async function updateTag(tagId: string, data: UpdateTagRequest): Promise<Tag> {
  const response = await apiClient.put<Tag>(`/tags/${tagId}`, data);
  return response.data;
}

/** Delete a tag. */
export async function deleteTag(tagId: string): Promise<void> {
  await apiClient.delete(`/tags/${tagId}`);
}
