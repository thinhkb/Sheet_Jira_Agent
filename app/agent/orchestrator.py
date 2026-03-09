from __future__ import annotations

from app.workflows.sync_sheet_to_jira import sync_sheet_to_jira
from app.workflows.sync_jira_to_sheet import sync_jira_to_sheet


class AgentOrchestrator:
    def __init__(self, sheets_client, jira_client, settings):
        self.sheets = sheets_client
        self.jira = jira_client
        self.settings = settings

    async def run_sync_sheet_to_jira(self):
        return await sync_sheet_to_jira(
            sheets=self.sheets,
            jira=self.jira,
            spreadsheet_id=self.settings.default_spreadsheet_id,
            sheet_name=self.settings.default_tasks_sheet,
            default_project_key=self.settings.default_jira_project_key,
            default_issue_type=self.settings.default_jira_issue_type,
        )

    async def run_sync_jira_to_sheet(self):
        return await sync_jira_to_sheet(
            sheets=self.sheets,
            jira=self.jira,
            spreadsheet_id=self.settings.default_spreadsheet_id,
            sheet_name=self.settings.default_tasks_sheet,
            project_key=self.settings.default_jira_project_key,
        )