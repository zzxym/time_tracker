/** Team-related TypeScript types. */

export interface TeamResponse {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  owner_username: string;
  created_at: string;
  updated_at: string;
  member_count: number;
}

export interface TeamMemberResponse {
  id: string;
  user_id: string;
  username: string;
  email: string;
  role: string;
  joined_at: string;
}

export interface TeamDetailResponse extends TeamResponse {
  members: TeamMemberResponse[];
}

export interface TeamMemberStatus {
  user_id: string;
  username: string;
  current_activity: string | null;
  current_activity_status: string | null;
  current_activity_started_at: string | null;
  today_duration_seconds: number;
}

export interface TeamActivityResponse {
  user_id: string;
  username: string;
  activity_id: string;
  activity_name: string;
  activity_status: string;
  started_at: string | null;
  today_duration_seconds: number;
}

export interface TeamStats {
  team_id: string;
  member_count: number;
  total_activities: number;
  total_duration_seconds: number;
  per_member: {
    user_id: string;
    username: string;
    activity_count: number;
    total_duration_seconds: number;
  }[];
}
