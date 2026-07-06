"""
Modelo de TipoMembresia — planes que ofrece el gimnasio (mensual, trimestral, etc.)
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import String, Integer, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TipoMembresia(Base):
    __tablename__ = "tipos_membresia"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    duracion_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # None = clases ilimitadas. Un número = tope de clases incluidas en el período.
    clases_incluidas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    membresias: Mapped[List["Membresia"]] = relationship(back_populates="tipo_membresia")

    def __repr__(self) -> str:
        return f"<TipoMembresia id={self.id} {self.nombre}>"
