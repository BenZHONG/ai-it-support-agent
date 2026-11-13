# agent.py

from tools import (
    check_device,
    check_user,
    create_ticket,
    search_knowledge_base,
)


def run_agent(
    employee_id: str,
    message: str,
) -> None:
    print(f"\nUser: {message}")

    # Step 1: Check employee
    user_result = check_user(employee_id)

    if not user_result["found"]:
        print("Agent: Employee not found.")
        return

    user = user_result["user"]

    if not user["active"]:
        print("Agent: Employee account is inactive.")
        return

    print(f"Agent: Hello {user['name']}.")

    # Step 2: Search knowledge base
    kb_result = search_knowledge_base(message)

    # Step 3: Check device
    device_result = check_device(user["device_id"])

    if not device_result["found"]:
        print("Agent: Device not found.")
        return

    device = device_result["device"]

    print(f"Agent: Device: {device['name']}")
    print(f"Agent: Wi-Fi adapter: {device['wifi_adapter']}")

    # Step 4: Recommend solution
    if kb_result["found"]:
        print("\nAgent: Please try these steps:")
        print(kb_result["solution"])
    else:
        print("Agent: No matching knowledge article found.")

    # Step 5: Ask whether the issue is resolved
    answer = input("\nDid this solve your problem? (yes/no): ")
    answer = answer.strip().lower()

    if answer == "yes":
        print("Agent: Great! Your issue is resolved.")

    elif answer == "no":
        confirmation = (
            input("Would you like me to create a support ticket? (yes/no): ")
            .strip()
            .lower()
        )

        if confirmation != "yes":
            print("Agent: No ticket was created.")
            return

        ticket = create_ticket(
            employee_id=employee_id,
            summary="Laptop Wi-Fi connection issue",
            description=message,
        )

        print(f"Agent: Ticket {ticket['ticket_id']} has been created.")

    else:
        print("Agent: Please reply yes or no.")
