"""
Punto de entrada de SARA GYM.
"""
import io
import sys

# Fix crítico para PyInstaller --windowed (aprendido en SARA POS): sin esto,
# ciertas librerías fallan en silencio porque stdout/stderr son None en builds windowed.
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

import bcrypt
from PySide6.QtWidgets import QApplication

from app.database.database import init_db, get_session
from app.models import Staff, RolStaff
from app.views.login_window import LoginWindow


def _crear_admin_default_si_no_existe() -> None:
    """Crea el usuario admin/123 la primera vez que se arranca la app."""
    session = get_session()
    try:
        existe = session.query(Staff).filter_by(usuario="admin").first()
        if existe is None:
            password_hash = bcrypt.hashpw("123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            admin = Staff(
                nombre="Administrador",
                apellido="",
                usuario="admin",
                password_hash=password_hash,
                rol=RolStaff.ADMIN,
                activo=True,
            )
            session.add(admin)
            session.commit()
    finally:
        session.close()


def main() -> None:
    init_db()
    _crear_admin_default_si_no_existe()

    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()