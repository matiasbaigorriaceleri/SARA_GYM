"""
Página de Dashboard: métricas clave del gimnasio de un vistazo.
"""
from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
)

from app.database.database import get_session
from app.models import Socio, Membresia, Pago, EstadoMembresia

COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_VERDE = "#3b8a3e"
COLOR_ROJO = "#c0451f"
COLOR_AMARILLO = "#b8860b"


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._build_ui()
        self._cargar_datos()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Dashboard")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Estado general del gimnasio")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        tarjetas_layout = QHBoxLayout()
        tarjetas_layout.setSpacing(14)

        self.tarjeta_activos = self._crear_tarjeta("Socios activos", COLOR_VERDE)
        self.tarjeta_vencidos = self._crear_tarjeta("Membresías vencidas", COLOR_ROJO)
        self.tarjeta_por_vencer = self._crear_tarjeta("Vencen en 7 días", COLOR_AMARILLO)
        self.tarjeta_ingresos_hoy = self._crear_tarjeta("Ingresos de hoy", COLOR_TEXTO)

        for tarjeta in (
            self.tarjeta_activos, self.tarjeta_vencidos,
            self.tarjeta_por_vencer, self.tarjeta_ingresos_hoy,
        ):
            tarjetas_layout.addWidget(tarjeta)

        layout.addLayout(tarjetas_layout)

        subtitulo_tabla = QLabel("Próximos vencimientos")
        subtitulo_tabla.setStyleSheet(
            f"color: {COLOR_TEXTO_MUTED}; font-size: 12px; font-weight: 500; margin-top: 8px;"
        )
        layout.addWidget(subtitulo_tabla)

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Socio", "Plan", "Vence"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.NoSelection)
        self.tabla.setStyleSheet(
            "QTableWidget { border: 1px solid #e5e2da; border-radius: 8px; background-color: white; }"
            "QHeaderView::section { background-color: #f1eee6; color: #8a8880; font-size: 12px;"
            " padding: 8px; border: none; }"
        )
        layout.addWidget(self.tabla, stretch=1)

    def _crear_tarjeta(self, etiqueta: str, color_valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #e5e2da; border-radius: 8px; }"
        )
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(18, 14, 18, 14)
        tarjeta_layout.setSpacing(4)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 12px;")
        tarjeta_layout.addWidget(label_etiqueta)

        label_valor = QLabel("-")
        label_valor.setStyleSheet(f"color: {color_valor}; font-size: 26px; font-weight: 700;")
        tarjeta_layout.addWidget(label_valor)

        tarjeta.label_valor = label_valor
        return tarjeta

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._cargar_datos()

    def _cargar_datos(self) -> None:
        session = get_session()
        try:
            hoy = date.today()
            en_7_dias = hoy + timedelta(days=7)

            todas = session.query(Membresia).all()
            for m in todas:
                if m.estado == EstadoMembresia.ACTIVA and m.fecha_vencimiento < hoy:
                    m.estado = EstadoMembresia.VENCIDA
            session.commit()

            cantidad_activos = (
                session.query(Membresia)
                .filter(Membresia.estado == EstadoMembresia.ACTIVA, Membresia.fecha_vencimiento >= hoy)
                .count()
            )
            cantidad_vencidos = session.query(Membresia).filter(Membresia.estado == EstadoMembresia.VENCIDA).count()

            por_vencer = (
                session.query(Membresia)
                .filter(
                    Membresia.estado == EstadoMembresia.ACTIVA,
                    Membresia.fecha_vencimiento >= hoy,
                    Membresia.fecha_vencimiento <= en_7_dias,
                )
                .order_by(Membresia.fecha_vencimiento)
                .all()
            )

            ingresos_hoy = (
                session.query(Pago)
                .filter(Pago.fecha >= hoy, Pago.fecha < hoy + timedelta(days=1))
                .all()
            )
            total_ingresos_hoy = sum(float(p.monto) for p in ingresos_hoy)

            self.tarjeta_activos.label_valor.setText(str(cantidad_activos))
            self.tarjeta_vencidos.label_valor.setText(str(cantidad_vencidos))
            self.tarjeta_por_vencer.label_valor.setText(str(len(por_vencer)))
            self.tarjeta_ingresos_hoy.label_valor.setText(f"${total_ingresos_hoy:,.0f}")

            self.tabla.setRowCount(len(por_vencer))
            for fila, m in enumerate(por_vencer):
                item_socio = QTableWidgetItem(m.socio.nombre_completo)
                item_plan = QTableWidgetItem(m.tipo_membresia.nombre)
                item_vence = QTableWidgetItem(m.fecha_vencimiento.strftime("%d/%m/%Y"))
                for item in (item_socio, item_plan, item_vence):
                    item.setForeground(QColor(COLOR_TEXTO))
                self.tabla.setItem(fila, 0, item_socio)
                self.tabla.setItem(fila, 1, item_plan)
                self.tabla.setItem(fila, 2, item_vence)

            self.tabla.resizeRowsToContents()
        finally:
            session.close()