from __future__ import annotations

from typing import Any

from app.mcp.base import MCPToolClient
from app.models import TaskRow


class GoogleSheetsMCPClient:
    def __init__(self, client: MCPToolClient):
        self.client = client

    async def list_spreadsheets(self) -> Any:
        return await self.client.call_tool("list_spreadsheets", {})

    async def list_sheets(self, spreadsheet_id: str) -> Any:
        return await self.client.call_tool(
            "list_sheets",
            {"spreadsheet_id": spreadsheet_id},
        )

    async def get_sheet_data(
        self,
        spreadsheet_id: str,
        sheet: str,
        cell_range: str = "A1:Z100",
    ) -> Any:
        return await self.client.call_tool(
            "get_sheet_data",
            {
                "spreadsheet_id": spreadsheet_id,
                "sheet": sheet,
                "range": cell_range,
            },
        )

    async def update_cells(
        self,
        spreadsheet_id: str,
        sheet: str,
        cell_range: str,
        values: list[list[Any]],
    ) -> Any:
        return await self.client.call_tool(
            "update_cells",
            {
                "spreadsheet_id": spreadsheet_id,
                "sheet": sheet,
                "range": cell_range,
                "values": values,
            },
        )

    def parse_task_rows(
        self,
        values: list[list[Any]],
        header_row_index: int = 0,
    ) -> list[TaskRow]:
        if not values or len(values) <= header_row_index:
            return []

        headers = [str(h).strip() for h in values[header_row_index]]
        rows: list[TaskRow] = []

        for idx, row in enumerate(values[header_row_index + 1 :], start=header_row_index + 2):
            row_map = {
                headers[i]: row[i] if i < len(row) else ""
                for i in range(len(headers))
            }

            task_name = str(row_map.get("task_name", "")).strip()
            if not task_name:
                continue

            rows.append(
                TaskRow(
                    row_number=idx,
                    task_id=str(row_map.get("task_id", "") or "") or None,
                    task_name=task_name,
                    description=str(row_map.get("description", "") or ""),
                    project_key=str(row_map.get("project_key", "") or "") or None,
                    issue_type=str(row_map.get("issue_type", "") or "") or None,
                    jira_issue_key=str(row_map.get("jira_issue_key", "") or "") or None,
                    sync_status=str(row_map.get("sync_status", "") or "") or None,
                    priority=str(row_map.get("priority", "") or "") or None,
                    assignee=str(row_map.get("assignee", "") or "") or None,
                    due_date=str(row_map.get("due_date", "") or "") or None,
                    status=str(row_map.get("status", "") or "") or None,
                    raw=row_map,
                )
            )

        return rows