"""SQLAlchemy model for employees. Indexes on employee_id and department support joins and usage-by-department analytics."""
from sqlalchemy import Column, Integer, String
from app.database import Base


class Employee(Base):
    """Employee dimension table (from CSV). Joined to telemetry by employee_id or email."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False)
    department = Column(String(128), nullable=False, index=True)
    role = Column(String(64), nullable=False)

    def __repr__(self) -> str:
        return f"<Employee {self.employee_id} {self.name}>"
