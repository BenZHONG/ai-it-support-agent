# agent.py

import json
from typing import Any

from openai import OpenAI

from config import get_api_key, get_model
from diagnosis import DiagnosisError, DiagnosisService
from schemas import (
    CreateTicketArgs,
    DiagnosisResult,
    EmployeeContext,
)
from ticket_workflow import TicketWorkflow
from tool_executor import ToolError, execute_tool
from workflow import Workflow, WorkflowState

MAX_TOOL_CALLS = 5
MAX_READ_ATTEMPTS = 2


class ITSupportAgent:
    """Stage 4: Workflow-controlled IT Support Agent."""

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
                max_retries=0,
            )
        )

        self.model = model or get_model()

        self.workflow = Workflow()
        self.ticket_workflow = TicketWorkflow()

        self.diagnosis_service = DiagnosisService(
            client=self.client,
            model=self.model,
        )

        self.problem: str | None = None
        self.diagnosis: DiagnosisResult | None = None
        self.evidence: dict[str, Any] = {}
        self.tool_calls_used = 0

    def start(self, message: str) -> str:
        """Start a new troubleshooting workflow."""

        message = message.strip()

        if not message:
            raise ValueError("Message cannot be empty.")

        if len(message) > 4000:
            raise ValueError("Message is too long.")

        if self.workflow.state != WorkflowState.NEW:
            return "A workflow already exists. Please finish or reset it."

        if not self.employee.authenticated:
            self.workflow.fail()
            return "Authentication required."

        self.problem = message
        self.tool_calls_used = 0
        self.evidence = {}

        try:
            # Step 1: Check employee.
            self.workflow.transition(WorkflowState.CHECKING_USER)

            user_result = self._read_tool(
                "check_user",
                {},
            )

            if not user_result["found"]:
                raise ToolError("Employee not found.")

            user = user_result["user"]

            if not user["active"]:
                raise ToolError("Employee is inactive.")

            self.evidence["user"] = user_result

            # Step 2: Search knowledge base.
            self.workflow.transition(WorkflowState.SEARCHING_KB)

            kb_result = self._read_tool(
                "search_knowledge_base",
                {"query": message},
                recoverable=True,
            )

            self.evidence["knowledge_base"] = kb_result

            # Step 3: Check assigned device.
            self.workflow.transition(WorkflowState.CHECKING_DEVICE)

            device_result = self._read_tool(
                "check_device",
                {"device_id": user["device_id"]},
                recoverable=True,
            )

            self.evidence["device"] = device_result

            # Step 4: Structured LLM diagnosis.
            self.workflow.transition(WorkflowState.DIAGNOSING)

            try:
                self.diagnosis = self.diagnosis_service.diagnose(
                    problem=message,
                    evidence=self.evidence,
                )
            except DiagnosisError:
                self.diagnosis = self._fallback_diagnosis()

            self.workflow.transition(WorkflowState.WAITING_FOR_FEEDBACK)

            return self._format_diagnosis()

        except (ToolError, KeyError, TypeError) as exc:
            self.workflow.fail()
            return f"I could not complete the troubleshooting workflow: {exc}"

    def _read_tool(
        self,
        name: str,
        arguments: dict,
        *,
        recoverable: bool = False,
    ) -> dict:
        """Execute a bounded, validated read-only tool."""

        last_error: ToolError | None = None

        for attempt in range(MAX_READ_ATTEMPTS):
            if self.tool_calls_used >= MAX_TOOL_CALLS:
                raise ToolError("Tool-call limit reached.")

            self.tool_calls_used += 1

            try:
                return execute_tool(
                    name=name,
                    arguments_json=json.dumps(arguments),
                    employee=self.employee,
                )

            except ToolError as exc:
                last_error = exc

                # Permission and authentication failures
                # must never be retried or ignored.
                if self._is_security_error(exc):
                    raise

                if attempt == MAX_READ_ATTEMPTS - 1:
                    break

        if recoverable:
            return {
                "found": False,
                "error": "Tool data unavailable",
            }

        raise last_error or ToolError("Tool execution failed.")

    @staticmethod
    def _is_security_error(error: ToolError) -> bool:
        text = str(error).lower()

        return any(
            phrase in text
            for phrase in (
                "authentication",
                "permission",
                "access denied",
                "inactive",
                "not allowed",
            )
        )

    def _fallback_diagnosis(self) -> DiagnosisResult:
        return DiagnosisResult(
            problem=self.problem or "IT support issue",
            likely_cause=(
                "The cause could not be determined from the available information."
            ),
            confidence="low",
            evidence=["Automated diagnosis was unavailable."],
            troubleshooting_steps=[
                "Check the network connection.",
                "Restart the laptop if appropriate.",
                "Contact IT support if the issue continues.",
            ],
            needs_escalation=True,
        )

    def _format_diagnosis(self) -> str:
        if self.diagnosis is None:
            return "No diagnosis is available."

        diagnosis = self.diagnosis

        steps = "\n".join(
            f"{index}. {step}"
            for index, step in enumerate(
                diagnosis.troubleshooting_steps,
                start=1,
            )
        )

        return (
            f"Problem: {diagnosis.problem}\n\n"
            f"Likely cause: {diagnosis.likely_cause}\n"
            f"Confidence: {diagnosis.confidence.value}\n\n"
            f"Recommended steps:\n{steps}\n\n"
            "Did these steps resolve the problem? "
            "Please answer yes or no."
        )

    def provide_feedback(self, resolved: bool) -> str:
        if self.workflow.state != WorkflowState.WAITING_FOR_FEEDBACK:
            raise ValueError("The workflow is not waiting for feedback.")

        if resolved:
            self.workflow.transition(WorkflowState.RESOLVED)
            return "Great! The issue is marked as resolved."

        if self.problem is None:
            self.workflow.fail()
            return "No active problem was found."

        description = (
            f"Employee reported: {self.problem}\n"
            f"Diagnosis: "
            f"{self.diagnosis.likely_cause if self.diagnosis else 'Unknown'}\n"
            "Troubleshooting did not resolve the issue."
        )

        args = CreateTicketArgs(
            summary=("IT issue: " + self.problem)[:200],
            description=description[:2000],
        )

        try:
            pending = self.ticket_workflow.prepare(
                self.employee,
                args,
            )

        except ToolError:
            self.workflow.fail()
            return (
                "I cannot prepare a support ticket. Please contact IT support directly."
            )

        self.workflow.transition(WorkflowState.WAITING_FOR_TICKET_CONFIRMATION)

        return (
            "I can create this support ticket:\n\n"
            f"Summary: {pending.summary}\n"
            f"Description: {pending.description}\n\n"
            "Type yes to confirm or no to cancel."
        )

    def confirm_ticket(self) -> str:
        if self.workflow.state != WorkflowState.WAITING_FOR_TICKET_CONFIRMATION:
            raise ValueError("No ticket is waiting for confirmation.")

        self.workflow.transition(WorkflowState.CREATING_TICKET)

        try:
            ticket = self.ticket_workflow.confirm(self.employee)

        except ToolError:
            self.workflow.fail()
            return "Ticket creation was not completed. Please contact IT support."

        self.workflow.transition(WorkflowState.ESCALATED)

        return (
            "Support ticket created successfully.\n"
            f"Ticket ID: {ticket['ticket_id']}\n"
            f"Status: {ticket['status']}"
        )

    def cancel_ticket(self) -> str:
        if self.workflow.state != WorkflowState.WAITING_FOR_TICKET_CONFIRMATION:
            raise ValueError("No ticket is waiting for confirmation.")

        self.ticket_workflow.cancel()

        self.workflow.transition(WorkflowState.WAITING_FOR_FEEDBACK)

        return "Ticket creation cancelled. No ticket was created."

    def reset(self) -> None:
        self.workflow.reset()
        self.ticket_workflow.cancel()

        self.problem = None
        self.diagnosis = None
        self.evidence = {}
        self.tool_calls_used = 0
