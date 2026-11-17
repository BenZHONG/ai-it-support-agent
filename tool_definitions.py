from copy import deepcopy
from typing import Any, TypeAlias

from openai.types.responses import FunctionToolParam
from pydantic import BaseModel

from schemas import (
    CreateTicketArgs,
    DeviceCheckArgs,
    EmptyArgs,
    KnowledgeSearchArgs,
    TicketStatusArgs,
)

# JSON Schema represented as a Python dictionary.
JSONSchema: TypeAlias = dict[str, Any]


def make_openai_schema(
    model_class: type[BaseModel],
) -> JSONSchema:
    """Convert a Pydantic model into an OpenAI-compatible schema."""

    schema: JSONSchema = deepcopy(model_class.model_json_schema())

    def clean(node: Any) -> None:
        if isinstance(node, dict):
            # Constraints enforced by Pydantic, not the LLM.
            for key in (
                "minLength",
                "maxLength",
                "minimum",
                "maximum",
                "pattern",
                "format",
            ):
                node.pop(key, None)

            for value in node.values():
                clean(value)

        elif isinstance(node, list):
            for value in node:
                clean(value)

    clean(schema)

    return schema


def function_tool(
    name: str,
    description: str,
    schema: type[BaseModel],
) -> FunctionToolParam:
    """Create a typed OpenAI Responses API function tool."""

    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": make_openai_schema(schema),
        "strict": True,
    }


READ_TOOLS: list[FunctionToolParam] = [
    function_tool(
        "check_user",
        "Get the current authenticated employee profile.",
        EmptyArgs,
    ),
    function_tool(
        "search_knowledge_base",
        "Search approved IT knowledge articles.",
        KnowledgeSearchArgs,
    ),
    function_tool(
        "check_device",
        "Check a company device assigned to the employee.",
        DeviceCheckArgs,
    ),
    function_tool(
        "get_ticket_status",
        "Get the status of an employee-owned ticket.",
        TicketStatusArgs,
    ),
]


CREATE_TICKET_TOOL: FunctionToolParam = function_tool(
    "create_ticket",
    "Propose a support ticket for employee confirmation.",
    CreateTicketArgs,
)


ALL_TOOLS: list[FunctionToolParam] = [
    *READ_TOOLS,
    CREATE_TICKET_TOOL,
]
