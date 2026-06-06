"""Export service for CSV, Excel, and JSON data export."""

import csv
import io
import json
from datetime import datetime
from typing import Optional

from openpyxl import Workbook


class ExportService:
    """Service for exporting activity data in various formats."""

    async def export_csv(self, activities: list[dict]) -> str:
        """Export activities as CSV string.

        Args:
            activities: List of activity dicts with keys:
                id, name, color, status, is_parallel, started_at, ended_at,
                total_duration_seconds, tags, created_at.

        Returns:
            CSV formatted string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Name", "Color", "Status", "Is Parallel",
            "Started At", "Ended At", "Duration (seconds)",
            "Tags", "Created At",
        ])

        for act in activities:
            tags_str = ", ".join(
                t.get("name", "") for t in act.get("tags", [])
            )
            writer.writerow([
                act.get("id", ""),
                act.get("name", ""),
                act.get("color", ""),
                act.get("status", ""),
                act.get("is_parallel", False),
                act.get("started_at", ""),
                act.get("ended_at", ""),
                act.get("total_duration_seconds", 0),
                tags_str,
                act.get("created_at", ""),
            ])

        return output.getvalue()

    async def export_excel(self, activities: list[dict]) -> bytes:
        """Export activities as Excel file bytes.

        Args:
            activities: List of activity dicts.

        Returns:
            Excel file content as bytes.
        """
        wb = Workbook()
        ws = wb.active
        ws.title = "Activities"

        # Header row
        headers = [
            "ID", "Name", "Color", "Status", "Is Parallel",
            "Started At", "Ended At", "Duration (seconds)",
            "Tags", "Created At",
        ]
        ws.append(headers)

        # Data rows
        for act in activities:
            tags_str = ", ".join(
                t.get("name", "") for t in act.get("tags", [])
            )
            ws.append([
                act.get("id", ""),
                act.get("name", ""),
                act.get("color", ""),
                act.get("status", ""),
                act.get("is_parallel", False),
                str(act.get("started_at", "")),
                str(act.get("ended_at", "")),
                act.get("total_duration_seconds", 0),
                tags_str,
                str(act.get("created_at", "")),
            ])

        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    cell_length = len(str(cell.value)) if cell.value else 0
                    if cell_length > max_length:
                        max_length = cell_length
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

        # Save to bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    async def export_json(self, activities: list[dict]) -> str:
        """Export activities as JSON string.

        Args:
            activities: List of activity dicts.

        Returns:
            JSON formatted string.
        """
        return json.dumps(activities, indent=2, default=str, ensure_ascii=False)
