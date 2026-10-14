
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    service: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_rate: Mapped[float] = mapped_column(Float, nullable=False)

    model_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    threshold_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False)
    decision_score: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    incident_id: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("incidents.id"),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    __table_args__ = (
        Index(
            "ix_telemetry_service_observed",
            "service",
            "observed_at",
        ),
    )
