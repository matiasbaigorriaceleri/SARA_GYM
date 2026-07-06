"""
Modelo de Clase — clases grupales dictadas por un instructor.
Funcionalidad de FASE 3 (GYM+), pero se modela desde ahora junto al resto.
"""
from __future__ import annotations

from datetime import time
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Clase(Base):
    __tablename__ = "clases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    instructor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"), nullable=True)

    # 0 = lunes ... 6 = domingo
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)

    cupo_max: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    instructor: Mapped[Optional["Staff"]] = relationship(back_populates="clases_dictadas")
    reservas: Mapped[List["Reserva"]] = relationship(
        back_populates="clase", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Clase id={self.id} {self.nombre}>"
