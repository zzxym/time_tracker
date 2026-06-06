/** Data export service for CSV, Excel, and JSON formats. */

import { saveAs } from 'file-saver';
import { exportActivities } from '../api/stats';
import type { ExportFormat } from '@time-tracker/shared';

/**
 * Export activity data and trigger a file download.
 */
export async function downloadExport(
  format: ExportFormat,
  startDate?: string,
  endDate?: string
): Promise<void> {
  const blob = await exportActivities(format, startDate, endDate);

  const extensions: Record<ExportFormat, string> = {
    csv: '.csv',
    excel: '.xlsx',
    json: '.json',
  };

  const mimeTypes: Record<ExportFormat, string> = {
    csv: 'text/csv',
    excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    json: 'application/json',
  };

  const fileName = `activities${extensions[format]}`;
  saveAs(blob, fileName);
}
