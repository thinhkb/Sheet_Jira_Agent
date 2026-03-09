from __future__ import annotations

import asyncio

from app.agent.orchestrator import AgentOrchestrator
from app.config import Settings
from app.mcp.http_client import HttpMCPClient
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

        agent = AgentOrchestrator(sheets_client, jira_client, settings)

        logger.info("Running real workflow: Sheet -> Jira")
        workflow_result = await agent.run_sync_sheet_to_jira()
        print(workflow_result.model_dump_json(indent=2))

    finally:
        if sheets_transport is not None:
            await sheets_transport.close()
        if jira_transport is not None:
            await jira_transport.close()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()