"""
Modelo de Socio — cliente del gimnasio.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import String, Date, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Socio(Base):
    __tablename__ = "socios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)
    dni: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)

    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    direccion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    foto_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    contacto_emergencia_nombre: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    contacto_emergencia_telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    observaciones: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fecha_alta: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relaciones
    membresias: Mapped[List["Membresia"]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )
    pagos: Mapped[List["Pago"]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )
    accesos: Mapped[List["Acceso"]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )
    reservas: Mapped[List["Reserva"]] = relationship(
        back_populates="socio", cascade="all, delete-orphan"
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self) -> str:
        return f"<Socio id={self.id} {self.nombre_completo}>"
