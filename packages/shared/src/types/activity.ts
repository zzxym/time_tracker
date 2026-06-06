// Activity / TimeSegment types
import type { Tag } from './tag';

export type ActivityStatus = 'RUNNING' | 'PAUSED' | 'ENDED';

export interface Activity {
  id: string;
  user_id: string;
  name: string;
  color: string;
  status: ActivityStatus;
  is_parallel: boolean;
  started_at: string;
  ended_at: string | null;
  total_duration_seconds: number;
  created_at: string;
  updated_at: string;
  tags?: Tag[];
  time_segments?: TimeSegment[];
}

export interface TimeSegment {
  id: string;
  activity_id: string;
  start_time: string;
  end_time: string | null;
}

export interface CreateActivityRequest {
  name: string;
  color?: string;
  is_parallel?: boolean;
  tag_ids?: string[];
}

export interface UpdateActivityRequest {
  name?: string;
  color?: string;
  is_parallel?: boolean;
  tag_ids?: string[];
}

export interface StartActivityRequest {
  parallel: boolean;
}
