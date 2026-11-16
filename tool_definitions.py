# tool_definitions.py

from copy import deepcopy

from schemas import (
    CreateTicketArgs,
    DeviceCheckArgs,
    EmptyArgs,
    KnowledgeSearchArgs,
    TicketStatusArgs,
)


def make_openai_schema(model_class):
    schema = deepcopy(model_class.model_json_schema())

    def clean(node):
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


def function_tool(name, description, schema):
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": make_openai_schema(schema),
        "strict": True,
    }


READ_TOOLS = [
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

CREATE_TICKET_TOOL = function_tool(
    "create_ticket",
    "Propose a support ticket for employee confirmation.",
    CreateTicketArgs,
)

ALL_TOOLS = [*READ_TOOLS, CREATE_TICKET_TOOL]
