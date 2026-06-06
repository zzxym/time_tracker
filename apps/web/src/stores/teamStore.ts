/** Zustand store for team management. */

import { create } from 'zustand';
import type { TeamResponse, TeamDetailResponse, TeamMemberResponse, TeamMemberStatus } from '../types/team';
import * as teamsApi from '../api/teams';

interface TeamStore {
  // List
  teams: TeamResponse[];
  loading: boolean;
  error: string;

  // Detail
  currentTeam: TeamDetailResponse | null;
  members: TeamMemberResponse[];
  memberStatuses: TeamMemberStatus[];

  // Actions
  fetchTeams: () => Promise<void>;
  fetchTeamDetail: (teamId: string) => Promise<void>;
  fetchMemberStatus: (teamId: string) => Promise<void>;
  createTeam: (name: string, description?: string) => Promise<TeamResponse>;
  updateTeam: (teamId: string, data: { name?: string; description?: string }) => Promise<void>;
  deleteTeam: (teamId: string) => Promise<void>;
  addMember: (teamId: string, userId: string, role?: string) => Promise<void>;
  removeMember: (teamId: string, userId: string) => Promise<void>;
  clearError: () => void;
}

export const useTeamStore = create<TeamStore>((set, get) => ({
  teams: [],
  loading: false,
  error: '',

  currentTeam: null,
  members: [],
  memberStatuses: [],

  fetchTeams: async () => {
    set({ loading: true, error: '' });
    try {
      const data = await teamsApi.getTeams();
      set({ teams: data, loading: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '获取团队列表失败';
      set({ error: msg, loading: false });
    }
  },

  fetchTeamDetail: async (teamId: string) => {
    set({ loading: true, error: '' });
    try {
      const data = await teamsApi.getTeamDetail(teamId);
      set({ currentTeam: data, members: data.members, loading: false });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '获取团队详情失败';
      set({ error: msg, loading: false });
    }
  },

  fetchMemberStatus: async (teamId: string) => {
    try {
      const data = await teamsApi.getTeamMemberStatus(teamId);
      set({ memberStatuses: data });
    } catch {
      // Silently fail for status polling
    }
  },

  createTeam: async (name: string, description?: string) => {
    set({ loading: true, error: '' });
    try {
      const data = await teamsApi.createTeam({ name, description: description || '' });
      set((s) => ({ teams: [data, ...s.teams], loading: false }));
      return data;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建团队失败';
      set({ error: msg, loading: false });
      throw e;
    }
  },

  updateTeam: async (teamId: string, data: { name?: string; description?: string }) => {
    set({ loading: true, error: '' });
    try {
      const updated = await teamsApi.updateTeam(teamId, data);
      set((s) => ({
        teams: s.teams.map((t) => (t.id === teamId ? updated : t)),
        currentTeam: s.currentTeam?.id === teamId ? { ...s.currentTeam, ...updated } : s.currentTeam,
        loading: false,
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '更新团队失败';
      set({ error: msg, loading: false });
      throw e;
    }
  },

  deleteTeam: async (teamId: string) => {
    set({ loading: true, error: '' });
    try {
      await teamsApi.deleteTeam(teamId);
      set((s) => ({
        teams: s.teams.filter((t) => t.id !== teamId),
        currentTeam: s.currentTeam?.id === teamId ? null : s.currentTeam,
        loading: false,
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '删除团队失败';
      set({ error: msg, loading: false });
      throw e;
    }
  },

  addMember: async (teamId: string, userId: string, role = 'member') => {
    try {
      const member = await teamsApi.addTeamMember(teamId, { user_id: userId, role });
      set((s) => ({ members: [...s.members, member] }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '添加成员失败';
      set({ error: msg });
      throw e;
    }
  },

  removeMember: async (teamId: string, userId: string) => {
    try {
      await teamsApi.removeTeamMember(teamId, userId);
      set((s) => ({
        members: s.members.filter((m) => m.user_id !== userId),
      }));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '移除成员失败';
      set({ error: msg });
      throw e;
    }
  },

  clearError: () => set({ error: '' }),
}));
