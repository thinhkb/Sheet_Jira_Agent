from __future__ import annotations

import asyncio

from app.agent.orchestrator import AgentOrchestrator
from app.config import Settings
from app.llm.gemini_agent import GeminiToolAgent
from app.llm.prompts import SYSTEM_PROMPT
from app.mcp.http_client import HttpMCPClient
from app.mcp.jira_client import JiraMCPClient
from app.mcp.sheets_client import GoogleSheetsMCPClient
from app.mcp.stdio_client import StdioMCPClient
from app.tools.raw_jira_tools import RawJiraTools
from app.tools.raw_sheet_tools import RawSheetTools
from app.tools.registry import ToolRegistry
from app.tools.sync_tools import SyncTools
from app.utils.logger import setup_logger


async def build_sheets_transport(settings: Settings) -> StdioMCPClient:
    client = StdioMCPClient(
        name="google-sheets",
        command=settings.google_sheets_command,
        args=[
            "--python=3.12",
            "mcp-google-sheets@latest",
            "--include-tools",
            "get_sheet_data,update_cells,list_spreadsheets,list_sheets",
        ],
        env={
            "SERVICE_ACCOUNT_PATH": settings.service_account_path,
        },
    )
    await client.connect()
    return client


async def build_jira_transport(settings: Settings):
    client = HttpMCPClient(
        url="http://127.0.0.1:9000/mcp",
        name="jira-http",
    )
    await client.connect()
    return client


async def async_main() -> None:
    logger = setup_logger()
    settings = Settings.from_env()
    settings.validate()

    sheets_transport = None
    jira_transport = None

    try:
        logger.info("Connecting Google Sheets MCP...")
        sheets_transport = await build_sheets_transport(settings)
        logger.info("Connected Google Sheets MCP")

        logger.info("Connecting Jira MCP...")
        jira_transport = await build_jira_transport(settings)
        logger.info("Connected Jira MCP")

        sheets_client = GoogleSheetsMCPClient(sheets_transport)
        jira_client = JiraMCPClient(jira_transport)

        orchestrator = AgentOrchestrator(sheets_client, jira_client, settings)

        raw_sheet_tools = RawSheetTools(
            sheets=sheets_client,
            spreadsheet_id=settings.default_spreadsheet_id,
            default_sheet=settings.default_tasks_sheet,
        )
        raw_jira_tools = RawJiraTools(
            jira=jira_client,
            default_project_key=settings.default_jira_project_key,
        )
        sync_tools = SyncTools(orchestrator)

        registry = ToolRegistry()
        registry.register("sheet_list_sheets", raw_sheet_tools.sheet_list_sheets)
        registry.register("sheet_get_data", raw_sheet_tools.sheet_get_data)
        registry.register("sheet_update_cells", raw_sheet_tools.sheet_update_cells)

        registry.register("jira_get_projects", raw_jira_tools.jira_get_projects)
        registry.register("jira_search_issues", raw_jira_tools.jira_search_issues)
        registry.register("jira_get_issue", raw_jira_tools.jira_get_issue)
        registry.register("jira_create_issue", raw_jira_tools.jira_create_issue)

        registry.register("sync_sheet_to_jira", sync_tools.sync_sheet_to_jira)
        registry.register("sync_jira_to_sheet", sync_tools.sync_jira_to_sheet)
        registry.register("get_sync_status", sync_tools.get_sync_status)

        agent = GeminiToolAgent(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
            tools=registry.get_all(),
        )

        print("Gemini MCP Agent started. Gõ 'exit' để thoát.\n")

        while True:
            user_input = input("Bạn: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break

            answer = await agent.run(user_input)
            print(f"\nAgent: {answer}\n")

    finally:
        if sheets_transport is not None:
            await sheets_transport.close()
        if jira_transport is not None:
            await jira_transport.close()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()