"""
Modelo de Staff — usuarios del sistema (administradores, recepción, instructores).
Cumple doble función: es tanto el "empleado" como el usuario que hace login.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RolStaff(str, enum.Enum):
    ADMIN = "admin"
    RECEPCION = "recepcion"
    INSTRUCTOR = "instructor"
    DUENO = "dueno"


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    apellido: Mapped[str] = mapped_column(String(80), nullable=False)

    usuario: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    rol: Mapped[RolStaff] = mapped_column(SAEnum(RolStaff), default=RolStaff.RECEPCION, nullable=False)

    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    clases_dictadas: Mapped[List["Clase"]] = relationship(back_populates="instructor")

    def __repr__(self) -> str:
        return f"<Staff id={self.id} usuario={self.usuario} rol={self.rol.value}>"
