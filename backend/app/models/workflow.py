from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class RemediationWorkflow(Base):
    __tablename__ = "remediation_workflows"

    incident_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("incidents.id"),
        primary_key=True,
    )
    approval_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING"
    )
    remediation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NOT_STARTED"
    )
    reviewer: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    decision_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    simulation_result: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )


class WorkflowAuditEvent(Base):
    __tablename__ = "workflow_audit_events"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )
    incident_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("incidents.id"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    actor: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    details: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
