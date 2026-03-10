from __future__ import annotations

from typing import Any

from app.mcp.sheets_client import GoogleSheetsMCPClient


class RawSheetTools:
    def __init__(self, sheets: GoogleSheetsMCPClient, spreadsheet_id: str, default_sheet: str):
        self.sheets = sheets
        self.spreadsheet_id = spreadsheet_id
        self.default_sheet = default_sheet

    async def sheet_list_sheets(self) -> dict[str, Any]:
        result = await self.sheets.list_sheets(self.spreadsheet_id)
        return {"spreadsheet_id": self.spreadsheet_id, "result": result}

    async def sheet_get_data(
        self,
        sheet_name: str | None = None,
        cell_range: str = "A1:L50",
    ) -> dict[str, Any]:
        result = await self.sheets.get_sheet_data(
            spreadsheet_id=self.spreadsheet_id,
            sheet=sheet_name or self.default_sheet,
            cell_range=cell_range,
        )
        return {
            "spreadsheet_id": self.spreadsheet_id,
            "sheet_name": sheet_name or self.default_sheet,
            "range": cell_range,
            "result": result,
        }

    async def sheet_update_cells(
        self,
        cell_range: str,
        data: list[list[Any]],
        sheet_name: str | None = None,
    ) -> dict[str, Any]:
        result = await self.sheets.update_cells(
            spreadsheet_id=self.spreadsheet_id,
            sheet=sheet_name or self.default_sheet,
            cell_range=cell_range,
            values=data,
        )
        return {
            "spreadsheet_id": self.spreadsheet_id,
            "sheet_name": sheet_name or self.default_sheet,
            "range": cell_range,
            "result": result,
        }