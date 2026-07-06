from __future__ import annotations

from typing import Any, Dict, Iterable

from .base import BaseTool, ToolExecutionContext, ToolExecutionResult, ToolSpec


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool] | None = None):
        self._tools: Dict[str, BaseTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        name = tool.spec.name
        if not name:
            raise ValueError("tool name cannot be empty")
        if name in self._tools:
            raise ValueError(f"tool already registered: {name}")
        self._tools[name] = tool

    def list_specs(self) -> list[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]

    def validate_call(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolExecutionResult(ok=False, error=f"unregistered tool: {tool_name}")

        args = arguments or {}
        schema = tool.spec.argument_schema or {}
        required = schema.get("required", [])
        for name in required:
            if name not in args:
                return ToolExecutionResult(ok=False, error=f"missing required argument: {name}")

        properties = schema.get("properties", {})
        for name, value in args.items():
            if name not in properties:
                continue
            expected_type = properties[name].get("type")
            if expected_type and not self._matches_json_type(value, expected_type):
                return ToolExecutionResult(
                    ok=False,
                    error=f"invalid argument type for {name}: expected {expected_type}",
                )
        return ToolExecutionResult(ok=True)

    def execute(self, tool_name: str, arguments: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        validation = self.validate_call(tool_name, arguments)
        if not validation.ok:
            return validation

        tool = self._tools[tool_name]
        try:
            return tool.execute(arguments or {}, context)
        except Exception as exc:
            return ToolExecutionResult(ok=False, error=f"tool execution failed: {exc}")

    @staticmethod
    def _matches_json_type(value: Any, expected_type: str | list[str]) -> bool:
        if isinstance(expected_type, list):
            return any(ToolRegistry._matches_json_type(value, item) for item in expected_type)
        if expected_type == "string":
            return isinstance(value, str)
        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "number":
            return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
        if expected_type == "boolean":
            return isinstance(value, bool)
        if expected_type == "object":
            return isinstance(value, dict)
        if expected_type == "array":
            return isinstance(value, list)
        return True
