# agent.py

import json
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from config import get_api_key, get_model
from prompts import IT_SUPPORT_SYSTEM_PROMPT
from schemas import EmployeeContext
from ticket_workflow import TicketWorkflow
from tool_definitions import ALL_TOOLS
from tool_executor import (
    ToolError,
    execute_tool,
    validate_arguments,
)

MAX_MODEL_ROUNDS = 6
MAX_TOOL_CALLS = 10
MAX_HISTORY_ITEMS = 40


class ITSupportAgent:
    def __init__(
        self,
        employee: EmployeeContext,
        client: Any | None = None,
        model: str | None = None,
    ) -> None:
        self.employee = employee

        self.client = (
            client
            if client is not None
            else OpenAI(
                api_key=get_api_key(),
                timeout=30.0,
                max_retries=2,
            )
        )

        self.model = model or get_model()

        self.history: list[Any] = []
        self.ticket_workflow = TicketWorkflow()

    def chat(self, message: str) -> str:
        message = message.strip()

        if not message:
            raise ValueError("Message cannot be empty.")

        if len(message) > 4000:
            raise ValueError("Message is too long.")

        if not self.employee.authenticated:
            return "Authentication required."

        # A pending proposal must be resolved before
        # the agent can start another model workflow.
        if self.ticket_workflow.pending is not None:
            return (
                "A ticket is waiting for confirmation. "
                "Please confirm or cancel it first."
            )

        conversation: list[Any] = [
            *self.history,
            {"role": "user", "content": message},
        ]

        tool_calls_used = 0

        try:
            for _ in range(MAX_MODEL_ROUNDS):
                response = self.client.responses.create(
                    model=self.model,
                    instructions=IT_SUPPORT_SYSTEM_PROMPT,
                    input=conversation,
                    tools=ALL_TOOLS,
                    tool_choice="auto",
                    parallel_tool_calls=False,
                    store=False,
                )

                # Preserve every returned response item.
                conversation.extend(response.output)

                function_calls = [
                    item for item in response.output if item.type == "function_call"
                ]

                if not function_calls:
                    answer = (response.output_text or "").strip()

                    if not answer:
                        return "I could not generate an answer. Please try again."

                    self._save_history(conversation)
                    return answer

                for call in function_calls:
                    tool_calls_used += 1

                    if tool_calls_used > MAX_TOOL_CALLS:
                        return (
                            "The troubleshooting process reached its tool-call limit."
                        )

                    result = self._handle_tool_call(call)

                    conversation.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(result),
                        }
                    )

                    # Stop before any ticket is created.
                    if self.ticket_workflow.pending is not None:
                        pending = self.ticket_workflow.pending

                        # Do not save an incomplete tool call
                        # sequence into conversation history.
                        return (
                            "I can create this support ticket:\n\n"
                            f"Summary: {pending.summary}\n"
                            f"Description: {pending.description}\n\n"
                            "Please confirm or cancel."
                        )

            return (
                "The troubleshooting process reached "
                "its maximum number of model rounds."
            )

        except RateLimitError:
            return "The AI service reached its usage limit."

        except (APIConnectionError, APITimeoutError):
            return "Unable to connect to the AI service."

        except APIStatusError:
            return "The AI service returned an error."

    def _handle_tool_call(self, call: Any) -> dict:
        try:
            if call.name == "create_ticket":
                args = validate_arguments(
                    call.name,
                    call.arguments,
                )

                self.ticket_workflow.prepare(
                    employee=self.employee,
                    args=args,
                )

                return {
                    "status": "confirmation_required",
                }

            return execute_tool(
                name=call.name,
                arguments_json=call.arguments,
                employee=self.employee,
            )

        except ToolError as error:
            return {
                "error": str(error),
            }

    def confirm_ticket(self) -> str:
        try:
            ticket = self.ticket_workflow.confirm(self.employee)

        except ToolError as error:
            return f"Ticket creation failed: {error}"

        return (
            "Support ticket created successfully.\n"
            f"Ticket ID: {ticket['ticket_id']}\n"
            f"Status: {ticket['status']}"
        )

    def cancel_ticket(self) -> str:
        self.ticket_workflow.cancel()
        return "Ticket creation cancelled."

    def reset_conversation(self) -> None:
        self.history.clear()
        self.ticket_workflow.cancel()

    def _save_history(
        self,
        conversation: list[Any],
    ) -> None:
        # Keep a bounded set of completed conversation turns.
        # More advanced context management comes in Stage 7.
        self.history = conversation[-MAX_HISTORY_ITEMS:]
