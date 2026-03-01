from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="team")
    models: Mapped[list["Model"]] = relationship(back_populates="team")