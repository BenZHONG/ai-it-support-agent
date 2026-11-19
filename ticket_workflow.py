# ticket_workflow.py

from dataclasses import dataclass

import tools
from schemas import CreateTicketArgs, EmployeeContext
from tool_executor import ToolError


@dataclass(frozen=True)
class PendingTicket:
    employee_id: str
    summary: str
    description: str


class TicketWorkflow:
    def __init__(self) -> None:
        self.pending: PendingTicket | None = None

    def prepare(
        self,
        employee: EmployeeContext,
        args: CreateTicketArgs,
    ) -> PendingTicket:
        if not employee.authenticated:
            raise ToolError("Authentication required.")

        if "ticket:create:self" not in employee.permissions:
            raise ToolError("Permission denied.")

        user_result = tools.check_user(employee.employee_id)

        if not user_result["found"] or not user_result["user"]["active"]:
            raise ToolError("Employee is not active.")

        self.pending = PendingTicket(
            employee_id=employee.employee_id,
            summary=args.summary,
            description=args.description,
        )

        return self.pending

    def confirm(self, employee: EmployeeContext) -> dict:
        pending = self.pending

        if pending is None:
            raise ToolError("No pending ticket.")

        if not employee.authenticated:
            raise ToolError("Authentication required.")

        if "ticket:create:self" not in employee.permissions:
            raise ToolError("Permission denied.")

        if pending.employee_id != employee.employee_id:
            raise ToolError("Employee mismatch.")

        user_result = tools.check_user(employee.employee_id)

        if not user_result["found"] or not user_result["user"]["active"]:
            raise ToolError("Employee is not active.")

        # Consume the proposal before the write operation.
        self.pending = None

        try:
            ticket = tools.create_ticket(
                employee_id=pending.employee_id,
                summary=pending.summary,
                description=pending.description,
            )

        except Exception as exc:
            raise ToolError(
                "Ticket backend failed; creation status "
                "may be unknown. Contact IT support."
            ) from exc

        return ticket

    def cancel(self) -> None:
        self.pending = None
