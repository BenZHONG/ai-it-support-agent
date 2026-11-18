from typing import Any

from openai import OpenAI

from config import get_api_key, get_model
from diagnosis import DiagnosisError, DiagnosisService
from schemas import (
    DiagnosisResult,
    EmployeeContext,
)
from ticket_workflow import TicketWorkflow
from tool_executor import ToolError
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
            return "A workflow already existes. Please finish or reset it."

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
