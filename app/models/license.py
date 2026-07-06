"""
Modelo de License — licencia activa del sistema.
Mismo esquema que SARA POS: clave HMAC-SHA256 formato GYM-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXX
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    license_key: Mapped[str] = mapped_column(String(60), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="FREE")  # FREE | GYM_PLUS

    fecha_activacion: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    activa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<License {self.license_key} tipo={self.tipo} activa={self.activa}>"
