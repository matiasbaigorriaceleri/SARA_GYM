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
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

from app.database.database import init_db, get_session
from app.models import Staff, RolStaff
from app.views.login_window import LoginWindow


def _aplicar_tema_claro(app: QApplication) -> None:
    """
    Fuerza un tema claro y consistente sin importar el tema del sistema operativo.
    Esto evita que Windows/Mac en modo oscuro dejen textos blancos sobre fondo
    blanco en diálogos nativos (QMessageBox, QDateEdit, etc.) que no tienen un
    estilo propio explícito. Se aplica UNA sola vez acá y cubre TODA la app,
    incluidos los diálogos que se agreguen en fases futuras.
    """
    app.setStyle("Fusion")
    paleta = QPalette()
    paleta.setColor(QPalette.Window, QColor("#faf8f4"))
    paleta.setColor(QPalette.WindowText, QColor("#2a2a2a"))
    paleta.setColor(QPalette.Base, QColor("#ffffff"))
    paleta.setColor(QPalette.AlternateBase, QColor("#f1eee6"))
    paleta.setColor(QPalette.Text, QColor("#2a2a2a"))
    paleta.setColor(QPalette.Button, QColor("#f1eee6"))
    paleta.setColor(QPalette.ButtonText, QColor("#2a2a2a"))
    paleta.setColor(QPalette.Highlight, QColor("#f05133"))
    paleta.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    paleta.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    paleta.setColor(QPalette.ToolTipText, QColor("#2a2a2a"))
    paleta.setColor(QPalette.PlaceholderText, QColor("#8a8880"))
    app.setPalette(paleta)


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
    _aplicar_tema_claro(app)

    login = LoginWindow()
    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()