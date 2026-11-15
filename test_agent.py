# test_agent.py

from unittest.mock import Mock

import pytest

from agent import ITSupportAgent


def make_agent(answer: str = "Please enable Wi-Fi."):
    """Create an agent with a fake OpenAI client."""

    client = Mock()

    client.responses.create.return_value.output_text = answer

    agent = ITSupportAgent(
        client=client,
        model="test-model",
    )

    return agent, client


def test_agent_returns_response():
    agent, client = make_agent()

    answer = agent.chat("My laptop cannot connect to Wi-Fi.")

    assert answer == "Please enable Wi-Fi."
    assert len(agent.history) == 2
    assert client.responses.create.call_count == 1


def test_empty_message_is_rejected():
    agent, client = make_agent()

    with pytest.raises(ValueError):
        agent.chat("   ")

    client.responses.create.assert_not_called()


def test_conversation_history():
    agent, client = make_agent()

    agent.chat("My laptop cannot connect to Wi-Fi.")
    agent.chat("Wi-Fi is disabled.")

    assert len(agent.history) == 4

    second_call = client.responses.create.call_args_list[1]
    conversation = second_call.kwargs["input"]

    assert len(conversation) == 3
    assert conversation[0]["role"] == "user"
    assert conversation[1]["role"] == "assistant"
    assert conversation[2]["content"] == "Wi-Fi is disabled."


def test_reset_conversation():
    agent, client = make_agent()

    agent.chat("Hello")
    agent.reset_conversation()

    assert agent.history == []


def test_empty_model_response_is_not_saved():
    agent, client = make_agent(answer="")

    answer = agent.chat("Hello")

    assert "could not generate" in answer
    assert agent.history == []


def test_model_does_not_receive_tools():
    agent, client = make_agent()

    agent.chat("Can you create a support ticket?")

    kwargs = client.responses.create.call_args.kwargs

    assert "tools" not in kwargs
    assert kwargs["store"] is False
