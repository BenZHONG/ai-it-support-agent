# schemas.py

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


class EmptyArgs(StrictModel):
    pass


class KnowledgeSearchArgs(StrictModel):
    query: str = Field(min_length=1, max_length=500)


class DeviceCheckArgs(StrictModel):
    device_id: str = Field(min_length=1, max_length=100)


class TicketStatusArgs(StrictModel):
    ticket_id: str = Field(min_length=1, max_length=100)


class CreateTicketArgs(StrictModel):
    summary: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=2000)


class EmployeeContext(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    employee_id: str
    authenticated: bool = True
    permissions: frozenset[str] = frozenset(
        {
            "user:read:self",
            "device:read:self",
            "knowledge:read",
            "ticket:read:self",
            "ticket:create:self",
        }
    )
