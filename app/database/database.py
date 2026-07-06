"""
Configuración de base de datos SQLite + SQLAlchemy para SARA GYM.
Sigue el mismo patrón que SARA POS:
  - echo=False SIEMPRE (con True el arranque tarda ~50s, ya lo sufrieron en SARA POS).
  - La base va en %APPDATA%\\SARA_GYM (Roaming) en Windows, NO en %LOCALAPPDATA%.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base


def _get_db_path() -> Path:
    """
    Devuelve la ruta de la base de datos según el SO.
    Windows: %APPDATA%\\SARA_GYM\\database.db
    Mac/Linux (entorno de desarrollo): ~/.sara_gym/database.db
    """
    if sys.platform == "win32":
        base_dir = Path(os.environ["APPDATA"]) / "SARA_GYM"
    else:
        base_dir = Path.home() / ".sara_gym"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "database.db"


DB_PATH = _get_db_path()
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Crea todas las tablas si no existen. Se llama una sola vez al arrancar la app."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Devuelve una nueva sesión. El caller es responsable de cerrarla (context manager o .close())."""
    return SessionLocal()
