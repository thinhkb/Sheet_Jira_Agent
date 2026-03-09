from __future__ import annotations

import asyncio
from asyncio.log import logger
import json

from app.agent.orchestrator import AgentOrchestrator
from app.config import Settings
from app.mcp.jira_client import JiraMCPClient
from app.mcp.sheets_client import GoogleSheetsMCPClient
from app.mcp.stdio_client import StdioMCPClient
from app.utils.logger import setup_logger


async def build_sheets_transport(settings: Settings) -> StdioMCPClient:
    client = StdioMCPClient(
        name="google-sheets",
        command=settings.google_sheets_command,
        args=[
            "--python=3.12",
            "mcp-google-sheets@latest",
            "--include-tools",
            "list_spreadsheets,list_sheets,get_sheet_data,update_cells",
        ],
        env={
            "SERVICE_ACCOUNT_PATH": settings.service_account_path,
        },
    )
    await client.connect()
    return client


async def build_jira_transport(settings: Settings) -> StdioMCPClient:
    client = StdioMCPClient(
        name="jira",
        command=settings.jira_command,
        args=[
            "--python=3.12",
            "mcp-atlassian",
        ],
        env={
            "JIRA_URL": settings.jira_url,
            "JIRA_USERNAME": settings.jira_username,
            "JIRA_API_TOKEN": settings.jira_api_token,

            # Chỉ bật đúng các tool cần cho bài toán hiện tại
            "ENABLED_TOOLS": ",".join([
                "jira_get_projects",
                "jira_search",
                "jira_get_issue",
                "jira_create_issue",
                "jira_update_issue",
                "jira_transition_issue",
            ]),

            # Debug
            "MCP_VERBOSE": "true",
            "MCP_VERY_VERBOSE": "true",

            # Giữ log ở stderr, không đẩy sang stdout vì stdout là kênh MCP protocol
            "MCP_LOGGING_STDOUT": "false",
        },
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

        sheets_tools = await sheets_transport.list_tools()
        logger.info("Google Sheets tools: %s", [t["name"] for t in sheets_tools])

        logger.info("Connecting Jira MCP...")
        jira_transport = await build_jira_transport(settings)
        logger.info("Connected Jira MCP")

        jira_tools = await jira_transport.list_tools()
        logger.info("Jira tools: %s", [t["name"] for t in jira_tools])
        logger.info("First Jira tools: %s", [t["name"] for t in jira_tools[:10]])

        sheets_client = GoogleSheetsMCPClient(sheets_transport)
        jira_client = JiraMCPClient(jira_transport)
        projects = await jira_client.get_projects()
        logger.info("Jira projects preview: %s", projects)
        agent = AgentOrchestrator(sheets_client, jira_client, settings)

        logger.info("Running real workflow: Sheet -> Jira")
        result = await agent.run_sync_sheet_to_jira()
        print(result.model_dump_json(indent=2))

    finally:
        if sheets_transport is not None:
            await sheets_transport.close()
        if jira_transport is not None:
            await jira_transport.close()

def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()