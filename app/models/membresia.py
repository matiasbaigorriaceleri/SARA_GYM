"""
Modelo de Membresia — vínculo entre un Socio y un TipoMembresia, con vigencia.
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class EstadoMembresia(str, enum.Enum):
    ACTIVA = "activa"
    VENCIDA = "vencida"
    SUSPENDIDA = "suspendida"
    CONGELADA = "congelada"


class Membresia(Base):
    __tablename__ = "membresias"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    tipo_membresia_id: Mapped[int] = mapped_column(ForeignKey("tipos_membresia.id"), nullable=False)

    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, nullable=False)

    estado: Mapped[EstadoMembresia] = mapped_column(
        SAEnum(EstadoMembresia), default=EstadoMembresia.ACTIVA, nullable=False
    )

    # Congelamiento (freeze) — funcionalidad de FASE 3, columnas listas desde ahora.
    fecha_congelamiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    dias_congelados: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    socio: Mapped["Socio"] = relationship(back_populates="membresias")
    tipo_membresia: Mapped["TipoMembresia"] = relationship(back_populates="membresias")
    pagos: Mapped[List["Pago"]] = relationship(back_populates="membresia")

    @property
    def esta_vigente(self) -> bool:
        return self.estado == EstadoMembresia.ACTIVA and self.fecha_vencimiento >= date.today()

    def __repr__(self) -> str:
        return f"<Membresia id={self.id} socio_id={self.socio_id} estado={self.estado.value}>"
