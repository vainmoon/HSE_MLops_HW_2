from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Integer, Index
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from typing import Optional
import enum

from database import Base


class VersionStatus(enum.Enum):
    staging = "staging"
    production = "production"
    archived = "archived"


class Model(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    task_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    team: Mapped["Team"] = relationship(back_populates="models")
    created_by_user: Mapped["User"] = relationship(back_populates="models")
    versions: Mapped[list["ModelVersion"]] = relationship(back_populates="model")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="model")


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[VersionStatus] = mapped_column(SAEnum(VersionStatus), default=VersionStatus.staging)
    artifact_path: Mapped[str] = mapped_column(String(500))
    training_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    model: Mapped["Model"] = relationship(back_populates="versions")
    created_by_user: Mapped["User"] = relationship(back_populates="versions")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="version")

    __table_args__ = (
        Index(
            "uq_one_production_per_model",
            "model_id",
            unique=True,
            postgresql_where=(status == VersionStatus.production),
        ),
    )