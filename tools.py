# tools.py

from uuid import uuid4

USERS = {
    "EMP001": {
        "employee_id": "EMP001",
        "name": "John Smith",
        "department": "Finance",
        "active": True,
        "device_id": "LAPTOP001",
    },
    "EMP002": {
        "employee_id": "EMP002",
        "name": "Sarah Lee",
        "department": "HR",
        "active": True,
        "device_id": "LAPTOP002",
    },
}

DEVICES = {
    "LAPTOP001": {
        "device_id": "LAPTOP001",
        "owner": "EMP001",
        "name": "Dell Latitude 5440",
        "status": "online",
        "wifi_adapter": "disabled",
    },
    "LAPTOP002": {
        "device_id": "LAPTOP002",
        "owner": "EMP002",
        "name": "HP EliteBook",
        "status": "online",
        "wifi_adapter": "enabled",
    },
}

KNOWLEDGE_BASE = {
    "wifi": {
        "title": "Troubleshoot Wi-Fi connectivity",
        "content": (
            "1. Open Windows Settings.\n"
            "2. Select Network & Internet.\n"
            "3. Check that Wi-Fi is enabled.\n"
            "4. Reconnect to the company network.\n"
            "5. If unresolved, contact IT support."
        ),
    }
}

TICKETS: dict[str, dict] = {}


def search_knowledge_base(query: str) -> dict:
    text = query.lower()

    if "wifi" in text or "wi-fi" in text:
        return {
            "found": True,
            "article": KNOWLEDGE_BASE["wifi"],
        }

    return {"found": False, "article": None}


def check_user(employee_id: str) -> dict:
    user = USERS.get(employee_id)

    return {
        "found": user is not None,
        "user": user,
    }


def check_device(device_id: str) -> dict:
    device = DEVICES.get(device_id)

    return {
        "found": device is not None,
        "device": device,
    }


def create_ticket(
    employee_id: str,
    summary: str,
    description: str,
) -> dict:
    ticket_id = f"INC-{uuid4().hex[:12].upper()}"

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
    ticket = TICKETS.get(ticket_id)

    return {
        "found": ticket is not None,
        "ticket": ticket,
    }
