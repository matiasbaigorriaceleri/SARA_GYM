"""
Modelo de Acceso — registro de cada intento de check-in en recepción.
En el MVP (FASE 1) se crea desde búsqueda manual; el resultado queda igual
registrado para poder auditar después quién entró y cuándo.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ResultadoAcceso(str, enum.Enum):
    PERMITIDO = "permitido"
    DENEGADO_VENCIDO = "denegado_vencido"
    DENEGADO_SUSPENDIDO = "denegado_suspendido"
    DENEGADO_NO_ENCONTRADO = "denegado_no_encontrado"


class Acceso(Base):
    __tablename__ = "accesos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nullable porque un intento "no encontrado" no tiene socio válido asociado.
    socio_id: Mapped[Optional[int]] = mapped_column(ForeignKey("socios.id"), nullable=True)

    resultado: Mapped[ResultadoAcceso] = mapped_column(SAEnum(ResultadoAcceso), nullable=False)
    observacion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    fecha_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    socio: Mapped[Optional["Socio"]] = relationship(back_populates="accesos")

    def __repr__(self) -> str:
        return f"<Acceso id={self.id} socio_id={self.socio_id} resultado={self.resultado.value}>"
