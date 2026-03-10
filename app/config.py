from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    jira_url: str
    jira_username: str
    jira_api_token: str

    service_account_path: str

    default_spreadsheet_id: str
    default_tasks_sheet: str
    default_jira_project_key: str
    default_jira_issue_type: str

    google_sheets_command: str
    jira_command: str

    gemini_api_key: str
    gemini_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            jira_url=os.getenv("JIRA_URL", ""),
            jira_username=os.getenv("JIRA_USERNAME", ""),
            jira_api_token=os.getenv("JIRA_API_TOKEN", ""),
            service_account_path=os.getenv("SERVICE_ACCOUNT_PATH", ""),
            default_spreadsheet_id=os.getenv("DEFAULT_SPREADSHEET_ID", ""),
            default_tasks_sheet=os.getenv("DEFAULT_TASKS_SHEET", "Tasks"),
            default_jira_project_key=os.getenv("DEFAULT_JIRA_PROJECT_KEY", "KAN"),
            default_jira_issue_type=os.getenv("DEFAULT_JIRA_ISSUE_TYPE", "Task"),
            google_sheets_command=os.getenv("GOOGLE_SHEETS_COMMAND", "uvx"),
            jira_command=os.getenv("JIRA_COMMAND", "uvx"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        )

    def validate(self) -> None:
        missing = []
        for key, value in {
            "JIRA_URL": self.jira_url,
            "JIRA_USERNAME": self.jira_username,
            "JIRA_API_TOKEN": self.jira_api_token,
            "SERVICE_ACCOUNT_PATH": self.service_account_path,
            "DEFAULT_SPREADSHEET_ID": self.default_spreadsheet_id,
            "GOOGLE_SHEETS_COMMAND": self.google_sheets_command,
            "JIRA_COMMAND": self.jira_command,
            "GEMINI_API_KEY": self.gemini_api_key,
            "GEMINI_MODEL": self.gemini_model,
        }.items():
            if not value:
                missing.append(key)

        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")