"""
Modelo de Pago — cobros registrados a un Socio (asociados o no a una Membresia).
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MetodoPago(str, enum.Enum):
    EFECTIVO = "efectivo"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    TRANSFERENCIA = "transferencia"
    MERCADOPAGO = "mercadopago"
    OTRO = "otro"


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    membresia_id: Mapped[Optional[int]] = mapped_column(ForeignKey("membresias.id"), nullable=True)

    monto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    metodo_pago: Mapped[MetodoPago] = mapped_column(SAEnum(MetodoPago), nullable=False)

    observaciones: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relaciones
    socio: Mapped["Socio"] = relationship(back_populates="pagos")
    membresia: Mapped[Optional["Membresia"]] = relationship(back_populates="pagos")

    def __repr__(self) -> str:
        return f"<Pago id={self.id} socio_id={self.socio_id} monto={self.monto}>"
