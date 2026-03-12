"""Pydantic schemas for employees."""
from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    """Payload for creating an employee record."""

    employee_id: str
    name: str
    email: str
    department: str
    role: str


class EmployeeResponse(BaseModel):
    """Employee as returned by the API."""

    id: int
    employee_id: str
    name: str
    email: str
    department: str
    role: str

    class Config:
        from_attributes = True
