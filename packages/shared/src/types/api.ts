// API response / WebSocket message types
import type { Activity } from './activity';
import type { Tag } from './tag';

export interface APIResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type WSMessageType =
  | 'activity_started'
  | 'activity_paused'
  | 'activity_resumed'
  | 'activity_stopped'
  | 'activity_updated'
  | 'tag_created'
  | 'tag_updated'
  | 'tag_deleted'
  | 'ping'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  payload: Record<string, unknown>;
}

export interface WSActivityPayload {
  activity: Activity;
  auto_paused?: Activity[];
}

export interface WSTagPayload {
  tag: Tag;
}

export interface StatsSummary {
  total_duration_seconds: number;
  activity_count: number;
  activities: ActivityStat[];
}

export interface ActivityStat {
  activity_id: string;
  activity_name: string;
  activity_color: string;
  total_duration_seconds: number;
  percentage: number;
}

export interface DateRange {
  start_date: string;
  end_date: string;
}

export type ExportFormat = 'csv' | 'excel' | 'json';
