"""
Ventana de login de SARA GYM.
Valida usuario/contraseña contra la tabla Staff (bcrypt). Estilo inspirado en
git-scm.com: fondo gris carbón (#2a2a2a) y acento naranja (#f05133).
"""
from __future__ import annotations

import bcrypt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame,
)

from app.database.database import get_session
from app.models import Staff

COLOR_FONDO = "#2a2a2a"
COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_TEXTO = "#f2f0ec"
COLOR_TEXTO_MUTED = "#a3a3a3"
COLOR_INPUT_BG = "#353535"
COLOR_INPUT_BORDER = "#454545"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SARA GYM — Iniciar sesión")
        self.setFixedSize(360, 280)
        self.setStyleSheet(f"background-color: {COLOR_FONDO};")
        self.main_window = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(14)

        titulo = QLabel("SARA GYM")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet(f"color: {COLOR_TEXTO}; font-size: 22px; font-weight: 500;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Iniciar sesión")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_INPUT_BORDER}; max-height: 1px; border: none;")
        layout.addWidget(linea)

        estilo_input = (
            f"QLineEdit {{ background-color: {COLOR_INPUT_BG}; color: {COLOR_TEXTO};"
            f" border: 1px solid {COLOR_INPUT_BORDER}; border-radius: 6px;"
            f" padding: 8px 12px; font-size: 13px; }}"
            f"QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}"
        )

        self.usuario_input = QLineEdit()
        self.usuario_input.setPlaceholderText("Usuario")
        self.usuario_input.setStyleSheet(estilo_input)
        layout.addWidget(self.usuario_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(estilo_input)
        self.password_input.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.password_input)

        self.boton_login = QPushButton("Ingresar")
        self.boton_login.setCursor(Qt.PointingHandCursor)
        self.boton_login.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_ACENTO}; color: {COLOR_FONDO};"
            f" border: none; border-radius: 6px; padding: 10px; font-size: 14px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {COLOR_ACENTO_HOVER}; }}"
        )
        self.boton_login.clicked.connect(self._intentar_login)
        layout.addWidget(self.boton_login)

        self.usuario_input.setFocus()

    def _intentar_login(self) -> None:
        usuario = self.usuario_input.text().strip()
        password = self.password_input.text()

        if not usuario or not password:
            QMessageBox.warning(self, "Datos incompletos", "Ingresá usuario y contraseña.")
            return

        session = get_session()
        try:
            staff = session.query(Staff).filter_by(usuario=usuario, activo=True).first()

            if staff is None or not bcrypt.checkpw(
                password.encode("utf-8"), staff.password_hash.encode("utf-8")
            ):
                QMessageBox.critical(self, "Error", "Usuario o contraseña incorrectos.")
                self.password_input.clear()
                self.password_input.setFocus()
                return

            self._abrir_main_window(staff)
        finally:
            session.close()

    def _abrir_main_window(self, staff: Staff) -> None:
        from app.views.main_window import MainWindow

        self.main_window = MainWindow(
            staff_nombre=f"{staff.nombre} {staff.apellido}".strip(),
            staff_rol=staff.rol.value,
        )
        self.main_window.show()
        self.close()