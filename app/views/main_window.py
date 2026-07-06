"""
Ventana principal de SARA GYM.
Estilo inspirado en git-scm.com: sidebar gris carbón (#2a2a2a) con acento
naranja (#f05133) para el ítem activo, contenido claro con títulos grandes.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame,
)

from app.views.pages.socios_page import SociosPage

COLOR_SIDEBAR = "#2a2a2a"
COLOR_ACENTO = "#f05133"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO_SIDEBAR = "#a3a3a3"
COLOR_SIDEBAR_HOVER = "#353535"
COLOR_CONTENIDO_BG = "#faf8f4"
COLOR_TEXTO_MUTED = "#8a8880"

MENU_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Socios", "socios"),
    ("Membresías", "membresias"),
    ("Pagos", "pagos"),
    ("Check-in", "checkin"),
    ("Clases", "clases"),
    ("Reportes", "reportes"),
    ("Configuración", "configuracion"),
]


class MainWindow(QMainWindow):
    def __init__(self, staff_nombre: str, staff_rol: str):
        super().__init__()
        self.setWindowTitle("SARA GYM")
        self.resize(1100, 700)

        self.staff_nombre = staff_nombre
        self.staff_rol = staff_rol
        self.paginas: dict[str, QWidget] = {}
        self.botones_menu: dict[str, QPushButton] = {}
        self.pagina_activa: str = "dashboard"
        self.login_window = None

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        central.setStyleSheet(f"background-color: {COLOR_CONTENIDO_BG};")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        for etiqueta, clave in MENU_ITEMS:
            if clave == "socios":
                pagina = SociosPage()
            else:
                pagina = self._crear_pagina_placeholder(etiqueta)
            self.paginas[clave] = pagina
            self.stack.addWidget(pagina)
        root_layout.addWidget(self.stack, stretch=1)

        self._mostrar_pagina("dashboard")

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet(f"background-color: {COLOR_SIDEBAR};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 20)
        sidebar_layout.setSpacing(2)

        logo = QLabel("SARA GYM")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("color: #f2f0ec; font-size: 16px; font-weight: 500; padding-bottom: 16px;")
        sidebar_layout.addWidget(logo)

        usuario_label = QLabel(f"{self.staff_nombre}\n({self.staff_rol})")
        usuario_label.setAlignment(Qt.AlignCenter)
        usuario_label.setStyleSheet(f"color: {COLOR_TEXTO_SIDEBAR}; font-size: 11px; padding-bottom: 16px;")
        sidebar_layout.addWidget(usuario_label)

        for etiqueta, clave in MENU_ITEMS:
            boton = QPushButton(etiqueta)
            boton.setCursor(Qt.PointingHandCursor)
            boton.setFlat(True)
            boton.setStyleSheet(self._estilo_boton(activo=False))
            boton.clicked.connect(lambda checked=False, c=clave: self._mostrar_pagina(c))
            sidebar_layout.addWidget(boton)
            self.botones_menu[clave] = boton

        sidebar_layout.addStretch()

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet("background-color: #3d3d3d; max-height: 1px; border: none;")
        sidebar_layout.addWidget(linea)

        boton_cerrar_sesion = QPushButton("Cerrar sesión")
        boton_cerrar_sesion.setCursor(Qt.PointingHandCursor)
        boton_cerrar_sesion.setFlat(True)
        boton_cerrar_sesion.setStyleSheet(self._estilo_boton(activo=False))
        boton_cerrar_sesion.clicked.connect(self._cerrar_sesion)
        sidebar_layout.addWidget(boton_cerrar_sesion)

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.setCursor(Qt.PointingHandCursor)
        boton_cerrar.setFlat(True)
        boton_cerrar.setStyleSheet(self._estilo_boton(activo=False))
        boton_cerrar.clicked.connect(self._cerrar_aplicacion)
        sidebar_layout.addWidget(boton_cerrar)

        return sidebar

    @staticmethod
    def _estilo_boton(activo: bool) -> str:
        if activo:
            return (
                f"QPushButton {{ color: {COLOR_ACENTO}; background-color: transparent; text-align: left;"
                f" padding: 9px 20px; border: none; outline: none;"
                f" border-left: 2px solid {COLOR_ACENTO}; font-size: 13px; font-weight: 500; }}"
            )
        return (
            f"QPushButton {{ color: {COLOR_TEXTO_SIDEBAR}; background-color: transparent; text-align: left;"
            f" padding: 9px 22px; border: none; outline: none; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_SIDEBAR_HOVER}; }}"
        )

    def _crear_pagina_placeholder(self, titulo: str) -> QWidget:
        pagina = QWidget()
        pagina.setStyleSheet(f"background-color: {COLOR_CONTENIDO_BG};")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(40, 40, 40, 40)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo_label)

        aviso = QLabel("Módulo en construcción — se implementa en las próximas fases del roadmap.")
        aviso.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(aviso)

        layout.addStretch()
        return pagina

    def _mostrar_pagina(self, clave: str) -> None:
        self.stack.setCurrentWidget(self.paginas[clave])
        self.botones_menu[self.pagina_activa].setStyleSheet(self._estilo_boton(activo=False))
        self.botones_menu[clave].setStyleSheet(self._estilo_boton(activo=True))
        self.pagina_activa = clave

    def _cerrar_sesion(self) -> None:
        from app.views.login_window import LoginWindow

        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def _cerrar_aplicacion(self) -> None:
        QApplication.quit()