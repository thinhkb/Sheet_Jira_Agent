from __future__ import annotations

from app.models import WorkflowResult
from app.mcp.sheets_client import GoogleSheetsMCPClient
from app.mcp.jira_client import JiraMCPClient


def _extract_values(sheet_data):
    if isinstance(sheet_data, dict):
        if "values" in sheet_data and isinstance(sheet_data["values"], list):
            return sheet_data["values"]
        if "result" in sheet_data and isinstance(sheet_data["result"], dict):
            return sheet_data["result"].get("values", [])
    return []


def _extract_issue_key(created):
    if isinstance(created, dict):
        if "key" in created:
            return created["key"]
        if "result" in created and isinstance(created["result"], dict):
            return created["result"].get("key")
    return None


async def sync_sheet_to_jira(
    sheets: GoogleSheetsMCPClient,
    jira: JiraMCPClient,
    spreadsheet_id: str,
    sheet_name: str,
    default_project_key: str,
    default_issue_type: str,
) -> WorkflowResult:
    result = WorkflowResult(ok=True, message="Sheet -> Jira sync finished")

    sheet_data = await sheets.get_sheet_data(
        spreadsheet_id=spreadsheet_id,
        sheet=sheet_name,
        cell_range="A1:Z200",
    )

    values = _extract_values(sheet_data)
    tasks = sheets.parse_task_rows(values)

    for task in tasks:
        try:
            if task.sync_status and task.sync_status.lower() == "synced":
                result.skipped += 1
                continue

            if task.jira_issue_key:
                result.skipped += 1
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "skip_existing_issue",
                    "jira_issue_key": task.jira_issue_key,
                })
                continue

            created = await jira.create_issue(
                project_key=task.project_key or default_project_key,
                summary=task.task_name,
                issue_type=task.issue_type or default_issue_type,
                description=task.description,
                priority=task.priority,
                assignee=task.assignee,
                due_date=task.due_date,
            )

            issue_key = _extract_issue_key(created)

            if issue_key:
                # G:H chỉ là ví dụ. Đổi lại theo layout sheet thật của bạn.
                await sheets.update_cells(
                    spreadsheet_id=spreadsheet_id,
                    sheet=sheet_name,
                    cell_range=f"G{task.row_number}:H{task.row_number}",
                    values=[[issue_key, "Synced"]],
                )

            result.created += 1
            result.details.append({
                "row": task.row_number,
                "task_name": task.task_name,
                "action": "created",
                "jira_issue_key": issue_key,
            })

        except Exception as exc:
            result.failed += 1
            result.ok = False
            result.details.append({
                "row": task.row_number,
                "task_name": task.task_name,
                "action": "failed",
                "error": str(exc),
            })

    return result