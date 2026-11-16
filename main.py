# main.py

from agent import ITSupportAgent
from schemas import EmployeeContext


def main() -> None:
    # Fictional authenticated employee.
    # Real authentication will be added in Stage 8.
    employee = EmployeeContext(
        employee_id="EMP001",
        authenticated=True,
    )

    agent = ITSupportAgent(employee=employee)

    print("=" * 55)
    print("AI IT SUPPORT AGENT - STAGE 3")
    print("=" * 55)
    print("Type 'exit' to quit.")
    print("Type 'reset' to clear the conversation.\n")

    while True:
        try:
            message = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if message.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if message.lower() == "reset":
            agent.reset_conversation()
            print("Agent: Conversation reset.\n")
            continue

        # Confirmation is handled by Python, not the LLM.
        if agent.ticket_workflow.pending is not None:
            if message.lower() == "yes":
                result = agent.confirm_ticket()
                print(f"\nAgent: {result}\n")

            elif message.lower() == "no":
                result = agent.cancel_ticket()
                print(f"\nAgent: {result}\n")

            else:
                print(
                    "\nAgent: Please type 'yes' to create "
                    "the ticket or 'no' to cancel.\n"
                )

            continue

        if not message:
            print("Agent: Please enter a message.\n")
            continue

        try:
            response = agent.chat(message)
            print(f"\nAgent: {response}\n")

        except ValueError as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()
