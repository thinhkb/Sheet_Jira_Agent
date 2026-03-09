from __future__ import annotations

from app.models import WorkflowResult
from app.mcp.sheets_client import GoogleSheetsMCPClient
from app.mcp.jira_client import JiraMCPClient


async def sync_jira_to_sheet(
    sheets: GoogleSheetsMCPClient,
    jira: JiraMCPClient,
    spreadsheet_id: str,
    sheet_name: str,
    project_key: str,
) -> WorkflowResult:
    result = WorkflowResult(ok=True, message="Jira -> Sheet sync finished")

    issues = await jira.search_issues(
        jql=f"project = {project_key} ORDER BY updated DESC",
        limit=20,
    )

    result.details.append({
        "action": "jira_search_done",
        "issues_preview": issues,
    })

    return result