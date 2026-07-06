"""
Diálogo de alta/edición de Membresia: asigna un Socio a un TipoMembresia con vigencia.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QDateEdit,
    QPushButton, QHBoxLayout, QMessageBox,
)

from app.models import Membresia, Socio, TipoMembresia, EstadoMembresia

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_FONDO_DIALOGO = "#ffffff"
COLOR_TEXTO = "#2a2a2a"
COLOR_BORDE = "#cfcac0"


class MembresiaFormDialog(QDialog):
    def __init__(self, session, membresia: Optional[Membresia] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._membresia = membresia
        self.setWindowTitle("Editar membresía" if membresia else "Nueva membresía")
        self.setMinimumWidth(400)
        self._aplicar_estilos()
        self._build_ui()
        self._cargar_combos()
        if membresia:
            self._cargar_datos(membresia)
        else:
            self.fecha_inicio_input.setDate(QDate.currentDate())
            self._recalcular_vencimiento()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO_DIALOGO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; background: transparent; }}
            QComboBox, QDateEdit {{
                background-color: {COLOR_FONDO_DIALOGO}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE}; border-radius: 6px;
                padding: 6px 8px; font-size: 13px;
            }}
            QComboBox:focus, QDateEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QComboBox QAbstractItemView {{
                background-color: {COLOR_FONDO_DIALOGO}; color: {COLOR_TEXTO};
                selection-background-color: {COLOR_ACENTO}; selection-color: white;
            }}
        """)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.socio_combo = QComboBox()
        self.tipo_combo = QComboBox()
        self.tipo_combo.currentIndexChanged.connect(self._recalcular_vencimiento)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_input.dateChanged.connect(self._recalcular_vencimiento)

        self.fecha_vencimiento_input = QDateEdit()
        self.fecha_vencimiento_input.setCalendarPopup(True)
        self.fecha_vencimiento_input.setDisplayFormat("dd/MM/yyyy")

        form.addRow("Socio *", self.socio_combo)
        form.addRow("Plan *", self.tipo_combo)
        form.addRow("Fecha de inicio *", self.fecha_inicio_input)
        form.addRow("Fecha de vencimiento *", self.fecha_vencimiento_input)

        layout.addLayout(form)

        botones = QHBoxLayout()
        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.setFlat(True)
        boton_cancelar.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {COLOR_TEXTO}; border: 1px solid {COLOR_BORDE};"
            f" border-radius: 6px; padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: #f1eee6; }}"
        )
        boton_cancelar.clicked.connect(self.reject)

        boton_guardar = QPushButton("Guardar")
        boton_guardar.setFlat(True)
        boton_guardar.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_ACENTO}; color: white; border: none;"
            f" border-radius: 6px; padding: 8px 20px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {COLOR_ACENTO_HOVER}; }}"
        )
        boton_guardar.clicked.connect(self._guardar)

        botones.addStretch()
        botones.addWidget(boton_cancelar)
        botones.addWidget(boton_guardar)
        layout.addLayout(botones)

    def _cargar_combos(self) -> None:
        socios = self._session.query(Socio).filter_by(activo=True).order_by(Socio.apellido, Socio.nombre).all()
        for socio in socios:
            self.socio_combo.addItem(socio.nombre_completo, userData=socio.id)

        tipos = self._session.query(TipoMembresia).filter_by(activo=True).order_by(TipoMembresia.nombre).all()
        for tipo in tipos:
            self.tipo_combo.addItem(f"{tipo.nombre} ({tipo.duracion_dias} días)", userData=tipo.id)

    def _recalcular_vencimiento(self) -> None:
        tipo_id = self.tipo_combo.currentData()
        if tipo_id is None:
            return
        tipo = self._session.get(TipoMembresia, tipo_id)
        if tipo is None:
            return
        qfecha_inicio = self.fecha_inicio_input.date()
        fecha_inicio = date(qfecha_inicio.year(), qfecha_inicio.month(), qfecha_inicio.day())
        fecha_vencimiento = fecha_inicio + timedelta(days=tipo.duracion_dias)
        self.fecha_vencimiento_input.setDate(
            QDate(fecha_vencimiento.year, fecha_vencimiento.month, fecha_vencimiento.day)
        )

    def _cargar_datos(self, membresia: Membresia) -> None:
        idx_socio = self.socio_combo.findData(membresia.socio_id)
        if idx_socio >= 0:
            self.socio_combo.setCurrentIndex(idx_socio)
        idx_tipo = self.tipo_combo.findData(membresia.tipo_membresia_id)
        if idx_tipo >= 0:
            self.tipo_combo.setCurrentIndex(idx_tipo)

        self.fecha_inicio_input.setDate(
            QDate(membresia.fecha_inicio.year, membresia.fecha_inicio.month, membresia.fecha_inicio.day)
        )
        self.fecha_vencimiento_input.setDate(
            QDate(membresia.fecha_vencimiento.year, membresia.fecha_vencimiento.month, membresia.fecha_vencimiento.day)
        )

    def _guardar(self) -> None:
        socio_id = self.socio_combo.currentData()
        tipo_id = self.tipo_combo.currentData()

        if socio_id is None or tipo_id is None:
            QMessageBox.warning(self, "Datos incompletos", "Elegí un socio y un plan.")
            return

        qinicio = self.fecha_inicio_input.date()
        qvencimiento = self.fecha_vencimiento_input.date()
        fecha_inicio = date(qinicio.year(), qinicio.month(), qinicio.day())
        fecha_vencimiento = date(qvencimiento.year(), qvencimiento.month(), qvencimiento.day())

        if fecha_vencimiento < fecha_inicio:
            QMessageBox.warning(self, "Fechas inválidas", "La fecha de vencimiento no puede ser anterior al inicio.")
            return

        if self._membresia is None:
            self._membresia = Membresia(
                socio_id=socio_id,
                tipo_membresia_id=tipo_id,
                fecha_inicio=fecha_inicio,
                fecha_vencimiento=fecha_vencimiento,
                estado=EstadoMembresia.ACTIVA,
            )
            self._session.add(self._membresia)
        else:
            self._membresia.socio_id = socio_id
            self._membresia.tipo_membresia_id = tipo_id
            self._membresia.fecha_inicio = fecha_inicio
            self._membresia.fecha_vencimiento = fecha_vencimiento

        self._session.commit()
        self.accept()