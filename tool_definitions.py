# tool_definitions.py

from schemas import (
    CreateTicketArgs,
    DeviceCheckArgs,
    EmptyArgs,
    KnowledgeSearchArgs,
    TicketStatusArgs,
)


def function_tool(name, description, schema):
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": schema.model_json_schema(),
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
        "Search approved company IT troubleshooting articles.",
        KnowledgeSearchArgs,
    ),
    function_tool(
        "check_device",
        "Check a company device assigned to the employee.",
        DeviceCheckArgs,
    ),
    function_tool(
        "get_ticket_status",
        "Get the status of an employee-owned IT ticket.",
        TicketStatusArgs,
    ),
]

CREATE_TICKET_TOOL = function_tool(
    "create_ticket",
    "Create a support ticket after explicit user confirmation.",
    CreateTicketArgs,
)

ALL_TOOLS = [*READ_TOOLS, CREATE_TICKET_TOOL]
