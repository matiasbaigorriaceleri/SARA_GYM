"""
Página de Membresías: pestaña "Membresías activas" (vista global de membresías
asignadas a socios) y pestaña "Planes" (tipos de membresía).
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from app.database.database import get_session
from app.models import Membresia, EstadoMembresia
from app.views.pages.tipos_membresia_page import TiposMembresiaPage
from app.views.dialogs.membresia_form_dialog import MembresiaFormDialog

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_VERDE = "#3b8a3e"
COLOR_ROJO = "#c0451f"
COLOR_AMARILLO = "#b8860b"

ESTADO_COLORES = {
    EstadoMembresia.ACTIVA: COLOR_VERDE,
    EstadoMembresia.VENCIDA: COLOR_ROJO,
    EstadoMembresia.SUSPENDIDA: COLOR_AMARILLO,
    EstadoMembresia.CONGELADA: COLOR_AMARILLO,
}


class MembresiasActivasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._build_ui()
        self._cargar_membresias()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(14)

        barra = QHBoxLayout()
        barra.addStretch()
        boton_nuevo = QPushButton("+ Nueva membresía")
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
        self.tabla.setHorizontalHeaderLabels(["Socio", "Plan", "Inicio", "Vencimiento", "Estado", ""])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
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
        self._cargar_membresias()

    def _cargar_membresias(self) -> None:
        session = get_session()
        try:
            membresias = (
                session.query(Membresia)
                .order_by(Membresia.fecha_vencimiento.desc())
                .all()
            )

            hoy = date.today()
            for m in membresias:
                if m.estado == EstadoMembresia.ACTIVA and m.fecha_vencimiento < hoy:
                    m.estado = EstadoMembresia.VENCIDA
            session.commit()

            self.tabla.setRowCount(len(membresias))

            for fila, m in enumerate(membresias):
                item_socio = QTableWidgetItem(m.socio.nombre_completo)
                item_plan = QTableWidgetItem(m.tipo_membresia.nombre)
                item_inicio = QTableWidgetItem(m.fecha_inicio.strftime("%d/%m/%Y"))
                item_vencimiento = QTableWidgetItem(m.fecha_vencimiento.strftime("%d/%m/%Y"))
                for item in (item_socio, item_plan, item_inicio, item_vencimiento):
                    item.setForeground(QColor(COLOR_TEXTO))

                item_estado = QTableWidgetItem(m.estado.value.capitalize())
                item_estado.setForeground(QColor(ESTADO_COLORES[m.estado]))

                self.tabla.setItem(fila, 0, item_socio)
                self.tabla.setItem(fila, 1, item_plan)
                self.tabla.setItem(fila, 2, item_inicio)
                self.tabla.setItem(fila, 3, item_vencimiento)
                self.tabla.setItem(fila, 4, item_estado)
                self.tabla.setCellWidget(fila, 5, self._crear_widget_acciones(m))

            self.tabla.resizeRowsToContents()
        finally:
            session.close()

    def _crear_widget_acciones(self, membresia: Membresia) -> QWidget:
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
        boton_editar.clicked.connect(lambda checked=False, mid=membresia.id: self._abrir_edicion(mid))
        fila_layout.addWidget(boton_editar)

        return contenedor

    def _abrir_alta(self) -> None:
        session = get_session()
        try:
            dialogo = MembresiaFormDialog(session=session, membresia=None, parent=self)
            if dialogo.exec():
                self._cargar_membresias()
        finally:
            session.close()

    def _abrir_edicion(self, membresia_id: int) -> None:
        session = get_session()
        try:
            membresia = session.get(Membresia, membresia_id)
            if membresia is None:
                return
            dialogo = MembresiaFormDialog(session=session, membresia=membresia, parent=self)
            if dialogo.exec():
                self._cargar_membresias()
        finally:
            session.close()


class MembresiasPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Membresías")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Planes ofrecidos y membresías asignadas a socios")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{
                background: transparent; color: {COLOR_TEXTO_MUTED};
                padding: 8px 16px; font-size: 13px; border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{ color: {COLOR_ACENTO}; border-bottom: 2px solid {COLOR_ACENTO}; }}
        """)

        self.tab_activas = MembresiasActivasTab()
        self.tab_planes = TiposMembresiaPage()

        self.tabs.addTab(self.tab_activas, "Membresías activas")
        self.tabs.addTab(self.tab_planes, "Planes")

        layout.addWidget(self.tabs, stretch=1)