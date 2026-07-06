"""
Modelo de Reserva — cupo de un Socio en una Clase para una fecha puntual.
Funcionalidad de FASE 3 (GYM+).
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EstadoReserva(str, enum.Enum):
    RESERVADA = "reservada"
    CANCELADA = "cancelada"
    ASISTIO = "asistio"
    AUSENTE = "ausente"


class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    clase_id: Mapped[int] = mapped_column(ForeignKey("clases.id"), nullable=False)

    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    estado: Mapped[EstadoReserva] = mapped_column(
        SAEnum(EstadoReserva), default=EstadoReserva.RESERVADA, nullable=False
    )

    observaciones: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    socio: Mapped["Socio"] = relationship(back_populates="reservas")
    clase: Mapped["Clase"] = relationship(back_populates="reservas")

    def __repr__(self) -> str:
        return f"<Reserva id={self.id} socio_id={self.socio_id} clase_id={self.clase_id}>"
