from __future__ import annotations

import json
from datetime import datetime

from app.models import WorkflowResult
from app.mcp.sheets_client import GoogleSheetsMCPClient
from app.mcp.jira_client import JiraMCPClient


def _extract_values(sheet_data):
    if not isinstance(sheet_data, dict):
        return []

    result = sheet_data.get("result")
    if not isinstance(result, dict):
        return []

    value_ranges = result.get("valueRanges")
    if isinstance(value_ranges, list) and value_ranges:
        vr = value_ranges[0]
        if isinstance(vr, dict):
            values = vr.get("values")
            if isinstance(values, list):
                return values

    return []


def _extract_issue_key(created):
    if not isinstance(created, dict):
        return None

    result = created.get("result")

    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except Exception:
            return None
    elif isinstance(result, dict):
        parsed = result
    else:
        return None

    issue = parsed.get("issue")
    if isinstance(issue, dict):
        return issue.get("key")

    return None


def _is_tool_error(value):
    if isinstance(value, str):
        lower = value.lower()
        return "validation error" in lower or "error" in lower

    if isinstance(value, dict):
        if "error" in value:
            return True

        result = value.get("result")
        if isinstance(result, str):
            lower = result.lower()
            return (
                "validation error" in lower
                or "error executing tool" in lower
                or "unexpected keyword argument" in lower
            )

    return False


def _normalize_priority(priority: str | None) -> str | None:
    if not priority:
        return None

    mapping = {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    return mapping.get(priority.strip().lower(), priority)


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _sheet_signature(task) -> tuple[str, str]:
    return (_normalize_text(task.project_id), _normalize_text(task.task_name))


def _extract_existing_jira_summaries(search_result) -> set[str]:
    """
    Cố gắng parse output từ jira_search.
    Hỗ trợ cả dict/object/string JSON.
    """
    summaries: set[str] = set()

    if search_result is None:
        return summaries

    data = search_result

    if isinstance(data, dict) and "result" in data and isinstance(data["result"], str):
        try:
            data = json.loads(data["result"])
        except Exception:
            return summaries

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return summaries

    if not isinstance(data, dict):
        return summaries

    issues = data.get("issues", [])
    if not isinstance(issues, list):
        return summaries

    for issue in issues:
        if not isinstance(issue, dict):
            continue

        summary = issue.get("summary")
        if isinstance(summary, str) and summary.strip():
            summaries.add(summary.strip().lower())
            continue

        fields = issue.get("fields")
        if isinstance(fields, dict):
            s = fields.get("summary")
            if isinstance(s, str) and s.strip():
                summaries.add(s.strip().lower())

    return summaries


async def _mark_sheet_status(
    sheets: GoogleSheetsMCPClient,
    spreadsheet_id: str,
    sheet_name: str,
    row_number: int,
    jira_issue_key: str,
    sync_status: str,
):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return await sheets.update_cells(
        spreadsheet_id=spreadsheet_id,
        sheet=sheet_name,
        cell_range=f"J{row_number}:L{row_number}",
        values=[[jira_issue_key, sync_status, now_str]],
    )


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
        cell_range="A1:L500",
    )

    values = _extract_values(sheet_data)
    tasks = sheets.parse_task_rows(values)

    if not tasks:
        return result

    # Lấy issue hiện có trong Jira để chống tạo trùng theo summary
    jira_existing = await jira.search_issues(
        jql=f'project = {default_project_key} ORDER BY created DESC',
        limit=200,
    )
    existing_jira_summaries = _extract_existing_jira_summaries(jira_existing)

    seen_sheet_signatures: set[tuple[str, str]] = set()

    for task in tasks:
        try:
            # 1) Skip nếu đã sync rồi
            if task.sync_status and task.sync_status.strip().lower() == "synced":
                result.skipped += 1
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "skip_synced",
                })
                continue

            # 2) Skip nếu đã có jira key
            if task.jira_issue_key:
                result.skipped += 1
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "skip_existing_issue_key",
                    "jira_issue_key": task.jira_issue_key,
                })
                continue

            # 3) Chống trùng trong cùng sheet batch
            signature = _sheet_signature(task)
            if signature in seen_sheet_signatures:
                await _mark_sheet_status(
                    sheets=sheets,
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    row_number=task.row_number,
                    jira_issue_key="",
                    sync_status="Duplicate in sheet",
                )
                result.skipped += 1
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "skip_duplicate_in_sheet",
                })
                continue
            seen_sheet_signatures.add(signature)

            # 4) Chống trùng với Jira theo summary
            normalized_summary = _normalize_text(task.task_name)
            if normalized_summary in existing_jira_summaries:
                await _mark_sheet_status(
                    sheets=sheets,
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    row_number=task.row_number,
                    jira_issue_key="",
                    sync_status="Already exists in Jira",
                )
                result.skipped += 1
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "skip_duplicate_in_jira",
                })
                continue

            created = await jira.create_issue(
                project_key=default_project_key,
                summary=task.task_name,
                issue_type=default_issue_type,
                description=task.description,
                priority=_normalize_priority(task.priority),
                due_date=task.due_date,
            )

            issue_key = _extract_issue_key(created)

            if _is_tool_error(created) or not issue_key:
                result.failed += 1
                result.ok = False
                result.details.append({
                    "row": task.row_number,
                    "task_name": task.task_name,
                    "action": "failed_create_issue",
                    "response": created,
                })
                continue

            update_resp = await _mark_sheet_status(
                sheets=sheets,
                spreadsheet_id=spreadsheet_id,
                sheet_name=sheet_name,
                row_number=task.row_number,
                jira_issue_key=issue_key,
                sync_status="Synced",
            )

            if isinstance(update_resp, dict) and "result" in update_resp:
                result_text = str(update_resp["result"]).lower()
                if "error" in result_text:
                    result.failed += 1
                    result.ok = False
                    result.details.append({
                        "row": task.row_number,
                        "task_name": task.task_name,
                        "action": "created_in_jira_but_failed_to_update_sheet",
                        "jira_issue_key": issue_key,
                        "update_response": update_resp,
                    })
                    continue

            existing_jira_summaries.add(normalized_summary)

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