from __future__ import annotations

import inspect
from typing import Any, Callable

from google import genai
from google.genai import types


class GeminiToolAgent:
    def __init__(
        self,
        api_key: str,
        model: str,
        system_instruction: str,
        tools: dict[str, Callable[..., Any]],
    ) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.system_instruction = system_instruction
        self.tools = tools

    async def run(self, user_message: str) -> str:
        contents: list[types.Content] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        ]

        declarations = self._tool_declarations()

        for _ in range(10):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=[types.Tool(function_declarations=declarations)],
                ),
            )

            candidate = response.candidates[0]
            parts = candidate.content.parts

            function_calls = [p.function_call for p in parts if getattr(p, "function_call", None)]

            if not function_calls:
                text_parts = [p.text for p in parts if getattr(p, "text", None)]
                return "\n".join(text_parts).strip()

            contents.append(candidate.content)

            tool_response_parts = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                if tool_name not in self.tools:
                    tool_result = {"error": f"Unknown tool: {tool_name}"}
                else:
                    fn = self.tools[tool_name]
                    if inspect.iscoroutinefunction(fn):
                        tool_result = await fn(**tool_args)
                    else:
                        tool_result = fn(**tool_args)

                tool_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_result},
                    )
                )

            contents.append(types.Content(role="tool", parts=tool_response_parts))

        return "Agent reached the maximum number of tool-calling steps."

    def _tool_declarations(self) -> list[types.FunctionDeclaration]:
        return [
            types.FunctionDeclaration(
                name="sheet_list_sheets",
                description="Liệt kê các tab trong spreadsheet mặc định.",
                parameters={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="sheet_get_data",
                description="Đọc dữ liệu từ một tab Google Sheet.",
                parameters={
                    "type": "object",
                    "properties": {
                        "sheet_name": {"type": "string", "description": "Tên tab, ví dụ Tasks"},
                        "cell_range": {"type": "string", "description": "Range, ví dụ A1:L50"},
                    },
                },
            ),
            types.FunctionDeclaration(
                name="sheet_update_cells",
                description="Cập nhật dữ liệu vào một range trong Google Sheet.",
                parameters={
                    "type": "object",
                    "properties": {
                        "sheet_name": {"type": "string"},
                        "cell_range": {"type": "string"},
                        "data": {
                            "type": "array",
                            "items": {"type": "array", "items": {}},
                            "description": "Mảng 2 chiều dữ liệu để ghi vào sheet",
                        },
                    },
                    "required": ["cell_range", "data"],
                },
            ),
            types.FunctionDeclaration(
                name="jira_get_projects",
                description="Lấy danh sách project Jira.",
                parameters={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="jira_search_issues",
                description="Tìm issue Jira bằng JQL.",
                parameters={
                    "type": "object",
                    "properties": {
                        "jql": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
            ),
            types.FunctionDeclaration(
                name="jira_get_issue",
                description="Lấy chi tiết một issue Jira theo key.",
                parameters={
                    "type": "object",
                    "properties": {
                        "issue_key": {"type": "string"},
                    },
                    "required": ["issue_key"],
                },
            ),
            types.FunctionDeclaration(
                name="jira_create_issue",
                description="Tạo một issue Jira mới trong project mặc định hoặc project chỉ định.",
                parameters={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "description": {"type": "string"},
                        "issue_type": {"type": "string"},
                        "project_key": {"type": "string"},
                    },
                    "required": ["summary"],
                },
            ),
            types.FunctionDeclaration(
                name="sync_sheet_to_jira",
                description="Đồng bộ các task từ Google Sheet sang Jira.",
                parameters={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="sync_jira_to_sheet",
                description="Đồng bộ các thay đổi từ Jira về lại Google Sheet.",
                parameters={"type": "object", "properties": {}},
            ),
            types.FunctionDeclaration(
                name="get_sync_status",
                description="Lấy thông tin cấu hình sync hiện tại.",
                parameters={"type": "object", "properties": {}},
            ),
        ]   