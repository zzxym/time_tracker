/** Team API client. */

import request from './client';
import type {
  TeamResponse,
  TeamDetailResponse,
  TeamMemberResponse,
  TeamMemberStatus,
  TeamActivityResponse,
  TeamStats,
} from '../types/team';

const BASE = '/api/teams';

/** 创建团队 */
export function createTeam(data: { name: string; description?: string }) {
  return request.post<TeamResponse>(BASE, data);
}

/** 获取我的团队列表 */
export function getTeams() {
  return request.get<TeamResponse[]>(BASE);
}

/** 获取团队详情（含成员） */
export function getTeamDetail(teamId: string) {
  return request.get<TeamDetailResponse>(`${BASE}/${teamId}`);
}

/** 更新团队信息 */
export function updateTeam(teamId: string, data: { name?: string; description?: string }) {
  return request.put<TeamResponse>(`${BASE}/${teamId}`, data);
}

/** 删除团队 */
export function deleteTeam(teamId: string) {
  return request.delete(`${BASE}/${teamId}`);
}

/** 添加成员 */
export function addTeamMember(teamId: string, data: { user_id: string; role?: string }) {
  return request.post<TeamMemberResponse>(`${BASE}/${teamId}/members`, data);
}

/** 更新成员角色 */
export function updateTeamMember(teamId: string, userId: string, role: string) {
  return request.put(`${BASE}/${teamId}/members/${userId}`, { role });
}

/** 移除成员 */
export function removeTeamMember(teamId: string, userId: string) {
  return request.delete(`${BASE}/${teamId}/members/${userId}`);
}

/** 获取团队成员实时状态 */
export function getTeamMemberStatus(teamId: string) {
  return request.get<TeamMemberStatus[]>(`${BASE}/${teamId}/status`);
}

/** 获取团队成员活动列表 */
export function getTeamActivities(teamId: string, params?: { start_date?: string; end_date?: string; user_id?: string }) {
  return request.get<TeamActivityResponse[]>(`${BASE}/${teamId}/activities`, { params });
}

/** 获取团队统计 */
export function getTeamStats(teamId: string, params?: { start_date?: string; end_date?: string }) {
  return request.get<TeamStats>(`${BASE}/${teamId}/stats`, { params });
}
