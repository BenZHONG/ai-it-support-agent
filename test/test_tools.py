# tests/test_tools.py

import json

import pytest

import tools
from schemas import EmployeeContext
from ticket_workflow import TicketWorkflow
from tool_executor import (
    ToolError,
    execute_tool,
    validate_arguments,
)


@pytest.fixture
def employee():
    return EmployeeContext(employee_id="EMP001")


def test_check_user(employee):
    result = execute_tool(
        "check_user",
        "{}",
        employee,
    )

    assert result["found"] is True
    assert result["user"]["employee_id"] == "EMP001"


def test_search_knowledge_base(employee):
    result = execute_tool(
        "search_knowledge_base",
        json.dumps({"query": "Wi-Fi problem"}),
        employee,
    )

    assert result["found"] is True


def test_check_own_device(employee):
    result = execute_tool(
        "check_device",
        json.dumps({"device_id": "LAPTOP001"}),
        employee,
    )

    assert result["found"] is True
    assert result["device"]["wifi_adapter"] == "disabled"


def test_cannot_check_other_employee_device(employee):
    with pytest.raises(ToolError, match="Device access denied"):
        execute_tool(
            "check_device",
            json.dumps({"device_id": "LAPTOP002"}),
            employee,
        )


def test_unknown_tool_is_rejected(employee):
    with pytest.raises(ToolError, match="not allowed"):
        execute_tool(
            "delete_all_devices",
            "{}",
            employee,
        )


def test_extra_arguments_are_rejected():
    with pytest.raises(ToolError):
        validate_arguments(
            "check_device",
            json.dumps(
                {
                    "device_id": "LAPTOP001",
                    "delete": True,
                }
            ),
        )


def test_invalid_argument_type_is_rejected():
    with pytest.raises(ToolError):
        validate_arguments(
            "check_device",
            json.dumps({"device_id": 123}),
        )


def test_invalid_json_is_rejected():
    with pytest.raises(ToolError):
        validate_arguments(
            "check_device",
            "{invalid-json}",
        )


def test_unauthenticated_employee_is_rejected():
    employee = EmployeeContext(
        employee_id="EMP001",
        authenticated=False,
    )

    with pytest.raises(ToolError, match="Authentication"):
        execute_tool("check_user", "{}", employee)


def test_create_ticket_requires_workflow(employee):
    with pytest.raises(ToolError, match="confirmed workflow"):
        execute_tool(
            "create_ticket",
            json.dumps(
                {
                    "summary": "Laptop Wi-Fi problem",
                    "description": "Laptop cannot connect to Wi-Fi.",
                }
            ),
            employee,
        )


def test_ticket_not_created_before_confirmation(employee):
    workflow = TicketWorkflow()
    before = len(tools.TICKETS)

    args = validate_arguments(
        "create_ticket",
        json.dumps(
            {
                "summary": "Laptop Wi-Fi problem",
                "description": "Laptop cannot connect to Wi-Fi.",
            }
        ),
    )

    workflow.prepare(employee, args)

    assert workflow.pending is not None
    assert len(tools.TICKETS) == before

    workflow.cancel()

    assert workflow.pending is None
    assert len(tools.TICKETS) == before


def test_ticket_created_after_confirmation(employee):
    workflow = TicketWorkflow()

    args = validate_arguments(
        "create_ticket",
        json.dumps(
            {
                "summary": "Laptop Wi-Fi problem",
                "description": "Laptop cannot connect to Wi-Fi.",
            }
        ),
    )

    workflow.prepare(employee, args)
    ticket = workflow.confirm(employee)

    try:
        assert ticket["employee_id"] == "EMP001"
        assert ticket["status"] == "open"
        assert ticket["ticket_id"] in tools.TICKETS

        with pytest.raises(ToolError, match="No pending"):
            workflow.confirm(employee)

    finally:
        tools.TICKETS.pop(ticket["ticket_id"], None)


def test_cannot_read_other_employee_ticket(employee):
    ticket = tools.create_ticket(
        employee_id="EMP002",
        summary="Other employee issue",
        description="A fictional support ticket.",
    )

    try:
        with pytest.raises(ToolError, match="Ticket access denied"):
            execute_tool(
                "get_ticket_status",
                json.dumps(
                    {
                        "ticket_id": ticket["ticket_id"],
                    }
                ),
                employee,
            )
    finally:
        tools.TICKETS.pop(ticket["ticket_id"], None)
