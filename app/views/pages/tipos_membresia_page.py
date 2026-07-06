"""
Página de gestión de Tipos de Membresía (planes): alta, edición y activar/desactivar.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from app.database.database import get_session
from app.models import TipoMembresia
from app.views.dialogs.tipo_membresia_form_dialog import TipoMembresiaFormDialog

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_VERDE = "#3b8a3e"
COLOR_ROJO = "#c0451f"


class TiposMembresiaPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._build_ui()
        self._cargar_tipos()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Planes de membresía")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Tipos de membresía que ofrece el gimnasio (mensual, trimestral, etc.)")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        barra = QHBoxLayout()
        barra.addStretch()

        boton_nuevo = QPushButton("+ Nuevo plan")
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

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Plan", "Duración", "Precio", "Clases incluidas", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.tabla.setColumnWidth(4, 190)
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
        self._cargar_tipos()

    def _cargar_tipos(self) -> None:
        session = get_session()
        try:
            tipos = session.query(TipoMembresia).order_by(TipoMembresia.nombre).all()
            self.tabla.setRowCount(len(tipos))

            for fila, tipo in enumerate(tipos):
                item_nombre = QTableWidgetItem(tipo.nombre)
                item_duracion = QTableWidgetItem(f"{tipo.duracion_dias} días")
                item_precio = QTableWidgetItem(f"${tipo.precio:,.2f}")
                item_clases = QTableWidgetItem(
                    str(tipo.clases_incluidas) if tipo.clases_incluidas is not None else "Ilimitadas"
                )
                for item in (item_nombre, item_duracion, item_precio, item_clases):
                    item.setForeground(QColor(COLOR_TEXTO))
                if not tipo.activo:
                    item_nombre.setForeground(QColor(COLOR_ROJO))

                self.tabla.setItem(fila, 0, item_nombre)
                self.tabla.setItem(fila, 1, item_duracion)
                self.tabla.setItem(fila, 2, item_precio)
                self.tabla.setItem(fila, 3, item_clases)
                self.tabla.setCellWidget(fila, 4, self._crear_widget_acciones(tipo))

            self.tabla.resizeRowsToContents()
        finally:
            session.close()

    def _crear_widget_acciones(self, tipo: TipoMembresia) -> QWidget:
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
        boton_editar.clicked.connect(lambda checked=False, tid=tipo.id: self._abrir_edicion(tid))
        fila_layout.addWidget(boton_editar)

        texto_boton = "Desactivar" if tipo.activo else "Reactivar"
        boton_toggle = QPushButton(texto_boton)
        boton_toggle.setCursor(Qt.PointingHandCursor)
        boton_toggle.setStyleSheet(estilo_boton)
        boton_toggle.clicked.connect(lambda checked=False, tid=tipo.id: self._toggle_activo(tid))
        fila_layout.addWidget(boton_toggle)

        return contenedor

    def _abrir_alta(self) -> None:
        session = get_session()
        try:
            dialogo = TipoMembresiaFormDialog(session=session, tipo=None, parent=self)
            if dialogo.exec():
                self._cargar_tipos()
        finally:
            session.close()

    def _abrir_edicion(self, tipo_id: int) -> None:
        session = get_session()
        try:
            tipo = session.get(TipoMembresia, tipo_id)
            if tipo is None:
                return
            dialogo = TipoMembresiaFormDialog(session=session, tipo=tipo, parent=self)
            if dialogo.exec():
                self._cargar_tipos()
        finally:
            session.close()

    def _toggle_activo(self, tipo_id: int) -> None:
        session = get_session()
        try:
            tipo = session.get(TipoMembresia, tipo_id)
            if tipo is None:
                return

            accion = "reactivar" if not tipo.activo else "desactivar"
            respuesta = QMessageBox.question(
                self, "Confirmar",
                f"¿Seguro que querés {accion} el plan \"{tipo.nombre}\"?",
            )
            if respuesta != QMessageBox.Yes:
                return

            tipo.activo = not tipo.activo
            session.commit()
            self._cargar_tipos()
        finally:
            session.close()