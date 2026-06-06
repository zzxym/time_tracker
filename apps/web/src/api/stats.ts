/** Statistics and export API functions. */

import apiClient from './client';
import type { StatsSummary, ExportFormat } from '@time-tracker/shared';

/** Get statistics summary for a time period. */
export async function getStatsSummary(params?: {
  period?: 'day' | 'week' | 'month';
  date?: string;
}): Promise<StatsSummary> {
  const response = await apiClient.get<StatsSummary>('/stats/summary', { params });
  return response.data;
}

/** Get export download URL. */
export function getExportUrl(format: ExportFormat, startDate?: string, endDate?: string): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
  const params = new URLSearchParams({ format });
  if (startDate) params.set('start_date', startDate);
  if (endDate) params.set('end_date', endDate);
  return `${baseUrl}/stats/export?${params.toString()}`;
}

/** Export activities as a downloadable blob. */
export async function exportActivities(
  format: ExportFormat,
  startDate?: string,
  endDate?: string
): Promise<Blob> {
  const params: Record<string, string> = { format };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  const response = await apiClient.get('/stats/export', {
    params,
    responseType: 'blob',
  });
  return response.data as Blob;
}
