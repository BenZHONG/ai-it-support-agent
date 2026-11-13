# tools.py

USERS = {
    "EMP001": {
        "name": "John Smith",
        "department": "Finance",
        "active": True,
        "device_id": "LAPTOP001",
    }
}

DEVICES = {
    "LAPTOP001": {
        "name": "Dell Latitude 5440",
        "status": "online",
        "wifi_adapter": "disabled",
    }
}

KNOWLEDGE_BASE = {
    "wifi": (
        "1. Open Windows Settings.\n"
        "2. Select Network & Internet.\n"
        "3. Enable Wi-Fi.\n"
        "4. Reconnect to the company network."
    )
}

TICKETS = {}


def search_knowledge_base(query: str) -> dict:
    """Search fictional IT knowledge articles."""
    if "wifi" in query.lower() or "wi-fi" in query.lower():
        return {
            "found": True,
            "solution": KNOWLEDGE_BASE["wifi"],
        }

    return {"found": False, "solution": None}


def check_user(employee_id: str) -> dict:
    """Retrieve fictional employee information."""
    user = USERS.get(employee_id)
    return {"found": user is not None, "user": user}


def check_device(device_id: str) -> dict:
    """Retrieve fictional device status."""
    device = DEVICES.get(device_id)
    return {"found": device is not None, "device": device}


def create_ticket(
    employee_id: str,
    summary: str,
    description: str,
) -> dict:
    """Create a fictional IT ticket."""
    ticket_id = f"INC{len(TICKETS) + 1:04d}"

    ticket = {
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "summary": summary,
        "description": description,
        "status": "open",
    }

    TICKETS[ticket_id] = ticket
    return ticket


def get_ticket_status(ticket_id: str) -> dict:
    """Retrieve the status of a fictional ticket."""
    ticket = TICKETS.get(ticket_id)

    if ticket is None:
        return {"found": False, "ticket": None}

    return {"found": True, "ticket": ticket}
