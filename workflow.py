# workflow.py

from dataclasses import dataclass, field
from enum import Enum


class WorkflowState(str, Enum):
    NEW = "new"
    CHECKING_USER = "checking_user"
    SEARCHING_KB = "searching_kb"
    CHECKING_DEVICE = "checking_device"
    DIAGNOSING = "diagnosing"
    WAITING_FOR_FEEDBACK = "waiting_for_feedback"
    WAITING_FOR_TICKET_CONFIRMATION = "waiting_for_ticket_confirmation"
    CREATING_TICKET = "creating_ticket"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


ALLOWED_TRANSITIONS = {
    WorkflowState.NEW: {
        WorkflowState.CHECKING_USER,
        WorkflowState.FAILED,
    },
    WorkflowState.CHECKING_USER: {
        WorkflowState.SEARCHING_KB,
        WorkflowState.FAILED,
    },
    WorkflowState.SEARCHING_KB: {
        WorkflowState.CHECKING_DEVICE,
        WorkflowState.FAILED,
    },
    WorkflowState.CHECKING_DEVICE: {
        WorkflowState.DIAGNOSING,
        WorkflowState.FAILED,
    },
    WorkflowState.DIAGNOSING: {
        WorkflowState.WAITING_FOR_FEEDBACK,
        WorkflowState.FAILED,
    },
    WorkflowState.WAITING_FOR_FEEDBACK: {
        WorkflowState.RESOLVED,
        WorkflowState.WAITING_FOR_TICKET_CONFIRMATION,
        WorkflowState.FAILED,
    },
    WorkflowState.WAITING_FOR_TICKET_CONFIRMATION: {
        WorkflowState.CREATING_TICKET,
        WorkflowState.WAITING_FOR_FEEDBACK,
        WorkflowState.FAILED,
    },
    WorkflowState.CREATING_TICKET: {
        WorkflowState.ESCALATED,
        WorkflowState.FAILED,
    },
    WorkflowState.RESOLVED: set(),
    WorkflowState.ESCALATED: set(),
    WorkflowState.FAILED: set(),
}


class WorkflowError(Exception):
    """Raised when a workflow transition is invalid."""


@dataclass
class Workflow:
    state: WorkflowState = WorkflowState.NEW
    history: list[WorkflowState] = field(default_factory=lambda: [WorkflowState.NEW])

    def transition(self, new_state: WorkflowState) -> None:
        allowed = ALLOWED_TRANSITIONS[self.state]

        if new_state not in allowed:
            raise WorkflowError(
                f"Invalid transition: {self.state.value} -> {new_state.value}"
            )

        self.state = new_state
        self.history.append(new_state)

    def fail(self) -> None:
        if self.state not in {
            WorkflowState.RESOLVED,
            WorkflowState.ESCALATED,
            WorkflowState.FAILED,
        }:
            self.transition(WorkflowState.FAILED)

    def reset(self) -> None:
        self.state = WorkflowState.NEW
        self.history = [WorkflowState.NEW]
