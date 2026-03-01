from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from typing import Optional
import enum

from database import Base


class AuditAction(enum.Enum):
    create_model = "create_model"
    create_version = "create_version"
    status_changed = "status_changed"


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[AuditAction] = mapped_column(SAEnum(AuditAction))
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    model_id: Mapped[int] = mapped_column(ForeignKey("models.id"))
    version_id: Mapped[Optional[int]] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    model: Mapped["Model"] = relationship(back_populates="audit_logs")
    version: Mapped[Optional["ModelVersion"]] = relationship(back_populates="audit_logs")
    user: Mapped["User"] = relationship(back_populates="audit_logs")