/** Tag state management with Zustand. */

import { create } from 'zustand';
import type { Tag } from '@time-tracker/shared';
import * as tagsApi from '../api/tags';

interface TagState {
  tags: Tag[];
  selectedTagIds: string[];
  isLoading: boolean;
  error: string | null;

  fetchTags: () => Promise<void>;
  createTag: (data: { name: string; color: string }) => Promise<Tag>;
  updateTag: (id: string, data: { name?: string; color?: string }) => Promise<void>;
  deleteTag: (id: string) => Promise<void>;
  toggleTagFilter: (tagId: string) => void;
  clearTagFilters: () => void;
}

export const useTagStore = create<TagState>()((set, get) => ({
  tags: [],
  selectedTagIds: [],
  isLoading: false,
  error: null,

  fetchTags: async () => {
    set({ isLoading: true, error: null });
    try {
      const tags = await tagsApi.listTags();
      set({ tags, isLoading: false });
    } catch (error) {
      set({ isLoading: false, error: String(error) });
    }
  },

  createTag: async (data) => {
    const tag = await tagsApi.createTag(data);
    set((state) => ({ tags: [tag, ...state.tags] }));
    return tag;
  },

  updateTag: async (id, data) => {
    const tag = await tagsApi.updateTag(id, data);
    set((state) => ({
      tags: state.tags.map((t) => (t.id === id ? tag : t)),
    }));
  },

  deleteTag: async (id) => {
    await tagsApi.deleteTag(id);
    set((state) => ({
      tags: state.tags.filter((t) => t.id !== id),
      selectedTagIds: state.selectedTagIds.filter((tid) => tid !== id),
    }));
  },

  toggleTagFilter: (tagId) => {
    set((state) => {
      const isSelected = state.selectedTagIds.includes(tagId);
      return {
        selectedTagIds: isSelected
          ? state.selectedTagIds.filter((id) => id !== tagId)
          : [...state.selectedTagIds, tagId],
      };
    });
  },

  clearTagFilters: () => {
    set({ selectedTagIds: [] });
  },
}));
