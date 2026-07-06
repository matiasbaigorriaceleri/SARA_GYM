"""
Página de Pagos: listado de cobros registrados, con alta y edición.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from app.database.database import get_session
from app.models import Pago
from app.views.dialogs.pago_form_dialog import PagoFormDialog, METODOS_LABELS

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"


class PagosPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._build_ui()
        self._cargar_pagos()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Pagos")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Registro de cobros a socios")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        barra = QHBoxLayout()
        self.buscador_input = QLineEdit()
        self.buscador_input.setPlaceholderText("Buscar por nombre o apellido del socio...")
        self.buscador_input.textChanged.connect(self._cargar_pagos)
        self.buscador_input.setStyleSheet(
            "QLineEdit { border: 1px solid #e5e2da; border-radius: 6px; padding: 8px 12px; font-size: 13px; }"
        )
        barra.addWidget(self.buscador_input, stretch=1)

        boton_nuevo = QPushButton("+ Nuevo pago")
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
        self.tabla.setHorizontalHeaderLabels(["Socio", "Plan", "Monto", "Método", "Fecha", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.tabla.setColumnWidth(5, 100)
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
        self._cargar_pagos()

    def _cargar_pagos(self) -> None:
        session = get_session()
        try:
            filtro = self.buscador_input.text().strip().lower()
            pagos = session.query(Pago).order_by(Pago.fecha.desc()).all()

            if filtro:
                pagos = [
                    p for p in pagos
                    if filtro in p.socio.nombre.lower() or filtro in p.socio.apellido.lower()
                ]

            self.tabla.setRowCount(len(pagos))

            for fila, pago in enumerate(pagos):
                item_socio = QTableWidgetItem(pago.socio.nombre_completo)
                nombre_plan = pago.membresia.tipo_membresia.nombre if pago.membresia else "-"
                item_plan = QTableWidgetItem(nombre_plan)
                item_monto = QTableWidgetItem(f"${pago.monto:,.2f}")
                item_metodo = QTableWidgetItem(METODOS_LABELS.get(pago.metodo_pago, pago.metodo_pago.value))
                item_fecha = QTableWidgetItem(pago.fecha.strftime("%d/%m/%Y"))
                for item in (item_socio, item_plan, item_monto, item_metodo, item_fecha):
                    item.setForeground(QColor(COLOR_TEXTO))

                self.tabla.setItem(fila, 0, item_socio)
                self.tabla.setItem(fila, 1, item_plan)
                self.tabla.setItem(fila, 2, item_monto)
                self.tabla.setItem(fila, 3, item_metodo)
                self.tabla.setItem(fila, 4, item_fecha)
                self.tabla.setCellWidget(fila, 5, self._crear_widget_acciones(pago))

            self.tabla.resizeRowsToContents()
        finally:
            session.close()

    def _crear_widget_acciones(self, pago: Pago) -> QWidget:
        contenedor = QWidget()
        fila_layout = QHBoxLayout(contenedor)
        fila_layout.setContentsMargins(4, 2, 4, 2)
        fila_layout.setSpacing(6)

        boton_editar = QPushButton("Editar")
        boton_editar.setCursor(Qt.PointingHandCursor)
        boton_editar.setStyleSheet(
            f"QPushButton {{ border: 1px solid #e5e2da; border-radius: 4px; padding: 4px 10px;"
            f" font-size: 12px; color: {COLOR_TEXTO}; background-color: white; }}"
            f"QPushButton:hover {{ background-color: #f1eee6; }}"
        )
        boton_editar.clicked.connect(lambda checked=False, pid=pago.id: self._abrir_edicion(pid))
        fila_layout.addWidget(boton_editar)

        return contenedor

    def _abrir_alta(self) -> None:
        session = get_session()
        try:
            dialogo = PagoFormDialog(session=session, pago=None, parent=self)
            if dialogo.exec():
                self._cargar_pagos()
        finally:
            session.close()

    def _abrir_edicion(self, pago_id: int) -> None:
        session = get_session()
        try:
            pago = session.get(Pago, pago_id)
            if pago is None:
                return
            dialogo = PagoFormDialog(session=session, pago=pago, parent=self)
            if dialogo.exec():
                self._cargar_pagos()
        finally:
            session.close()