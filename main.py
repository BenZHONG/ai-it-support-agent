# main.py

from agent import ITSupportAgent


def main() -> None:
    print("=" * 50)
    print("AI IT SUPPORT AGENT - STAGE 2")
    print("=" * 50)

    print("Type 'exit' to quit.")
    print("Type 'reset' to start a new conversation.\n")

    agent = ITSupportAgent()

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
            print("Agent: Conversation cleared.\n")
            continue

        if not message:
            print("Agent: Please enter a message.\n")
            continue

        try:
            answer = agent.chat(message)
            print(f"\nAgent: {answer}\n")

        except ValueError as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()
