# tool_executor.py

import json
from typing import Any

from pydantic import ValidationError

import tools
from schemas import (
    CreateTicketArgs,
    DeviceCheckArgs,
    EmployeeContext,
    EmptyArgs,
    KnowledgeSearchArgs,
    TicketStatusArgs,
)


class ToolError(Exception):
    pass


TOOL_SCHEMAS = {
    "check_user": EmptyArgs,
    "search_knowledge_base": KnowledgeSearchArgs,
    "check_device": DeviceCheckArgs,
    "get_ticket_status": TicketStatusArgs,
    "create_ticket": CreateTicketArgs,
}

TOOL_PERMISSIONS = {
    "check_user": "user:read:self",
    "search_knowledge_base": "knowledge:read",
    "check_device": "device:read:self",
    "get_ticket_status": "ticket:read:self",
    "create_ticket": "ticket:create:self",
}

ALLOWED_TOOLS = frozenset(TOOL_SCHEMAS)


def validate_arguments(
    name: str,
    arguments_json: str,
) -> Any:
    if name not in ALLOWED_TOOLS:
        raise ToolError("Tool is not allowed.")

    try:
        arguments = json.loads(arguments_json)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ToolError("Invalid tool JSON.") from exc

    if not isinstance(arguments, dict):
        raise ToolError("Tool arguments must be an object.")

    try:
        return TOOL_SCHEMAS[name].model_validate(arguments)
    except ValidationError as exc:
        raise ToolError("Invalid tool arguments.") from exc


def execute_tool(
    name: str,
    arguments_json: str,
    employee: EmployeeContext,
) -> dict:
    """Validate, authorise and execute a read-only tool."""

    if name not in ALLOWED_TOOLS:
        raise ToolError("Tool is not allowed.")

    if not employee.authenticated:
        raise ToolError("Authentication required.")

    permission = TOOL_PERMISSIONS[name]

    if permission not in employee.permissions:
        raise ToolError("Permission denied.")

    args = validate_arguments(name, arguments_json)

    # Ticket creation has a separate confirmation workflow.
    if name == "create_ticket":
        raise ToolError("Ticket creation requires a confirmed workflow.")

    if name == "check_user":
        return tools.check_user(employee.employee_id)

    if name == "search_knowledge_base":
        return tools.search_knowledge_base(args.query)

    if name == "check_device":
        user_result = tools.check_user(employee.employee_id)

        if not user_result["found"]:
            raise ToolError("Employee not found.")

        user = user_result["user"]

        if not user["active"]:
            raise ToolError("Employee is inactive.")

        if user["device_id"] != args.device_id:
            raise ToolError("Device access denied.")

        device_result = tools.check_device(args.device_id)

        if (
            device_result["found"]
            and device_result["device"]["owner"] != employee.employee_id
        ):
            raise ToolError("Device access denied.")

        return device_result

    if name == "get_ticket_status":
        result = tools.get_ticket_status(args.ticket_id)

        if not result["found"]:
            return {"found": False, "ticket": None}

        if result["ticket"]["employee_id"] != employee.employee_id:
            raise ToolError("Ticket access denied.")

        return result

    raise ToolError("Tool is not implemented.")
