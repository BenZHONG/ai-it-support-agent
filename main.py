# main.py

from agent import ITSupportAgent
from schemas import EmployeeContext
from workflow import WorkflowState


def main() -> None:
    # Fictional authenticated employee.
    # Real authentication comes in Stage 8.
    employee = EmployeeContext(
        employee_id="EMP001",
        authenticated=True,
    )

    agent = ITSupportAgent(employee=employee)

    print("=" * 55)
    print("AI IT SUPPORT AGENT - STAGE 4")
    print("=" * 55)

    print("Commands:")
    print("  reset - Start a new workflow")
    print("  exit  - Quit the application\n")

    while True:
        try:
            message = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        command = message.lower()

        if command in {"exit", "quit"}:
            print("Goodbye!")
            break

        if command == "reset":
            agent.reset()
            print("Agent: Workflow reset.\n")
            continue

        if not message:
            print("Agent: Please enter a message.\n")
            continue

        state = agent.workflow.state

        try:
            if state == WorkflowState.NEW:
                response = agent.start(message)

            elif state == WorkflowState.WAITING_FOR_FEEDBACK:
                if command == "yes":
                    response = agent.provide_feedback(True)

                elif command == "no":
                    response = agent.provide_feedback(False)

                else:
                    response = (
                        "Please type yes if the issue is resolved, or no if it is not."
                    )

            elif state == (WorkflowState.WAITING_FOR_TICKET_CONFIRMATION):
                if command == "yes":
                    response = agent.confirm_ticket()

                elif command == "no":
                    response = agent.cancel_ticket()

                else:
                    response = "Please type yes to create the ticket or no to cancel."

            else:
                response = (
                    f"Current workflow state: {state.value}\n"
                    "Type reset to start a new incident."
                )

            print(f"\nAgent: {response}\n")

        except ValueError as exc:
            print(f"\nError: {exc}\n")


if __name__ == "__main__":
    main()
