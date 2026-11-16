# tests/test_agent.py

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import tools
from agent import ITSupportAgent
from schemas import EmployeeContext


def function_call(name, arguments, call_id="call_1"):
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
        call_id=call_id,
    )


def make_response(output, text=""):
    return SimpleNamespace(
        output=output,
        output_text=text,
    )


@pytest.fixture
def employee():
    return EmployeeContext(employee_id="EMP001")


def test_agent_executes_device_tool(employee):
    client = Mock()

    client.responses.create.side_effect = [
        make_response(
            [
                function_call(
                    "check_device",
                    {"device_id": "LAPTOP001"},
                )
            ]
        ),
        make_response(
            [],
            "Your Wi-Fi adapter is disabled.",
        ),
    ]

    agent = ITSupportAgent(
        employee=employee,
        client=client,
        model="test-model",
    )

    answer = agent.chat("My laptop cannot connect to Wi-Fi.")

    assert "disabled" in answer
    assert client.responses.create.call_count == 2

    second_request = client.responses.create.call_args_list[1].kwargs

    outputs = [
        item
        for item in second_request["input"]
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]

    assert len(outputs) == 1

    tool_result = json.loads(outputs[0]["output"])
    assert tool_result["device"]["wifi_adapter"] == "disabled"


def test_agent_previews_ticket_without_creating(employee):
    client = Mock()

    client.responses.create.return_value = make_response(
        [
            function_call(
                "create_ticket",
                {
                    "summary": "Laptop Wi-Fi problem",
                    "description": ("Laptop cannot connect to company Wi-Fi."),
                },
            )
        ]
    )

    agent = ITSupportAgent(
        employee=employee,
        client=client,
        model="test-model",
    )

    before = len(tools.TICKETS)

    answer = agent.chat("Please create a ticket for my Wi-Fi problem.")

    assert "Please confirm or cancel" in answer
    assert len(tools.TICKETS) == before
    assert agent.ticket_workflow.pending is not None


def test_agent_creates_ticket_only_after_confirmation(employee):
    client = Mock()

    client.responses.create.return_value = make_response(
        [
            function_call(
                "create_ticket",
                {
                    "summary": "Laptop Wi-Fi problem",
                    "description": ("Laptop cannot connect to company Wi-Fi."),
                },
            )
        ]
    )

    agent = ITSupportAgent(
        employee=employee,
        client=client,
        model="test-model",
    )

    agent.chat("Please create a ticket.")

    result = agent.confirm_ticket()

    created = [ticket_id for ticket_id in tools.TICKETS if ticket_id in result]

    try:
        assert len(created) == 1
        assert "created successfully" in result

        second_result = agent.confirm_ticket()
        assert "No pending ticket" in second_result

    finally:
        for ticket_id in created:
            tools.TICKETS.pop(ticket_id, None)


def test_agent_rejects_empty_message(employee):
    client = Mock()

    agent = ITSupportAgent(
        employee=employee,
        client=client,
        model="test-model",
    )

    with pytest.raises(ValueError):
        agent.chat("   ")

    client.responses.create.assert_not_called()


def test_reset_cancels_pending_ticket(employee):
    client = Mock()

    client.responses.create.return_value = make_response(
        [
            function_call(
                "create_ticket",
                {
                    "summary": "Laptop Wi-Fi problem",
                    "description": ("Laptop cannot connect to company Wi-Fi."),
                },
            )
        ]
    )

    agent = ITSupportAgent(
        employee=employee,
        client=client,
        model="test-model",
    )

    agent.chat("Create a ticket.")
    agent.reset_conversation()

    assert agent.ticket_workflow.pending is None
    assert agent.history == []
