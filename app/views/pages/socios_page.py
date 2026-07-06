"""
Página de gestión de Socios: alta, baja (activar/desactivar) y modificación.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from app.database.database import get_session
from app.models import Socio
from app.views.dialogs.socio_form_dialog import SocioFormDialog

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_VERDE = "#3b8a3e"
COLOR_ROJO = "#c0451f"


class SociosPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._build_ui()
        self._cargar_socios()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Socios")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Gestión de socios del gimnasio")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        barra = QHBoxLayout()
        self.buscador_input = QLineEdit()
        self.buscador_input.setPlaceholderText("Buscar por nombre, apellido o DNI...")
        self.buscador_input.textChanged.connect(self._cargar_socios)
        self.buscador_input.setStyleSheet(
            "QLineEdit { border: 1px solid #e5e2da; border-radius: 6px; padding: 8px 12px; font-size: 13px; }"
        )
        barra.addWidget(self.buscador_input, stretch=1)

        boton_nuevo = QPushButton("+ Nuevo socio")
        boton_nuevo.setCursor(Qt.PointingHandCursor)
        boton_nuevo.setFlat(True)
        boton_nuevo.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_ACENTO}; color: white; border: none;"
            f" border-radius: 6px; padding: 8px 18px; font-weight: 500; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_ACENTO_HOVER}; }}"
        )
        boton_nuevo.clicked.connect(self._abrir_alta)
        barra.addWidget(boton_nuevo)

        layout.addLayout(barra)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "DNI", "Teléfono", "Email", "Estado", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tabla.setColumnWidth(5, 190)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setStyleSheet(
            "QTableWidget { border: 1px solid #e5e2da; border-radius: 8px; background-color: white; }"
            "QHeaderView::section { background-color: #f1eee6; color: #8a8880; font-size: 12px;"
            " padding: 8px; border: none; }"
        )
        layout.addWidget(self.tabla, stretch=1)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._cargar_socios()

    def _cargar_socios(self) -> None:
        session = get_session()
        try:
            filtro = self.buscador_input.text().strip().lower()
            socios = session.query(Socio).order_by(Socio.apellido, Socio.nombre).all()

            if filtro:
                socios = [
                    s for s in socios
                    if filtro in s.nombre.lower()
                    or filtro in s.apellido.lower()
                    or (s.dni and filtro in s.dni.lower())
                ]

            self.tabla.setRowCount(len(socios))

            for fila, socio in enumerate(socios):
                item_nombre = QTableWidgetItem(socio.nombre_completo)
                item_dni = QTableWidgetItem(socio.dni or "-")
                item_telefono = QTableWidgetItem(socio.telefono or "-")
                item_email = QTableWidgetItem(socio.email or "-")
                for item in (item_nombre, item_dni, item_telefono, item_email):
                    item.setForeground(QColor(COLOR_TEXTO))

                self.tabla.setItem(fila, 0, item_nombre)
                self.tabla.setItem(fila, 1, item_dni)
                self.tabla.setItem(fila, 2, item_telefono)
                self.tabla.setItem(fila, 3, item_email)

                estado_item = QTableWidgetItem("Activo" if socio.activo else "Inactivo")
                estado_item.setForeground(QColor(COLOR_VERDE if socio.activo else COLOR_ROJO))
                self.tabla.setItem(fila, 4, estado_item)

                self.tabla.setCellWidget(fila, 5, self._crear_widget_acciones(socio))

            self.tabla.resizeRowsToContents()
        finally:
            session.close()

    def _crear_widget_acciones(self, socio: Socio) -> QWidget:
        contenedor = QWidget()
        fila_layout = QHBoxLayout(contenedor)
        fila_layout.setContentsMargins(4, 2, 4, 2)
        fila_layout.setSpacing(6)

        estilo_boton = (
            f"QPushButton {{ border: 1px solid #e5e2da; border-radius: 4px; padding: 4px 10px;"
            f" font-size: 12px; color: {COLOR_TEXTO}; background-color: white; }}"
            f"QPushButton:hover {{ background-color: #f1eee6; }}"
        )

        boton_editar = QPushButton("Editar")
        boton_editar.setCursor(Qt.PointingHandCursor)
        boton_editar.setStyleSheet(estilo_boton)
        boton_editar.clicked.connect(lambda checked=False, sid=socio.id: self._abrir_edicion(sid))
        fila_layout.addWidget(boton_editar)

        texto_boton = "Dar de baja" if socio.activo else "Reactivar"
        boton_baja = QPushButton(texto_boton)
        boton_baja.setCursor(Qt.PointingHandCursor)
        boton_baja.setStyleSheet(estilo_boton)
        boton_baja.clicked.connect(lambda checked=False, sid=socio.id: self._toggle_activo(sid))
        fila_layout.addWidget(boton_baja)

        return contenedor

    def _abrir_alta(self) -> None:
        session = get_session()
        try:
            dialogo = SocioFormDialog(session=session, socio=None, parent=self)
            if dialogo.exec():
                self._cargar_socios()
        finally:
            session.close()

    def _abrir_edicion(self, socio_id: int) -> None:
        session = get_session()
        try:
            socio = session.get(Socio, socio_id)
            if socio is None:
                return
            dialogo = SocioFormDialog(session=session, socio=socio, parent=self)
            if dialogo.exec():
                self._cargar_socios()
        finally:
            session.close()

    def _toggle_activo(self, socio_id: int) -> None:
        session = get_session()
        try:
            socio = session.get(Socio, socio_id)
            if socio is None:
                return

            accion = "reactivar" if not socio.activo else "dar de baja a"
            respuesta = QMessageBox.question(
                self, "Confirmar",
                f"¿Seguro que querés {accion} a {socio.nombre_completo}?",
            )
            if respuesta != QMessageBox.Yes:
                return

            socio.activo = not socio.activo
            session.commit()
            self._cargar_socios()
        finally:
            session.close()