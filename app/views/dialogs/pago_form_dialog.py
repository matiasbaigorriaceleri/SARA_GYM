"""
Diálogo de alta/edición de Pago.
Al elegir un socio, se listan sus membresías (para asociar el pago a una en
particular) y se autocompleta el monto con el precio del plan seleccionado.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QDateEdit,
    QPushButton, QHBoxLayout, QMessageBox,
)

from app.models import Pago, Socio, Membresia, MetodoPago

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_FONDO_DIALOGO = "#ffffff"
COLOR_TEXTO = "#2a2a2a"
COLOR_BORDE = "#cfcac0"

SIN_MEMBRESIA = -1

METODOS_LABELS = {
    MetodoPago.EFECTIVO: "Efectivo",
    MetodoPago.TARJETA_DEBITO: "Tarjeta de débito",
    MetodoPago.TARJETA_CREDITO: "Tarjeta de crédito",
    MetodoPago.TRANSFERENCIA: "Transferencia",
    MetodoPago.MERCADOPAGO: "Mercado Pago",
    MetodoPago.OTRO: "Otro",
}


class PagoFormDialog(QDialog):
    def __init__(self, session, pago: Optional[Pago] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._pago = pago
        self.setWindowTitle("Editar pago" if pago else "Nuevo pago")
        self.setMinimumWidth(400)
        self._aplicar_estilos()
        self._build_ui()
        self._cargar_socios()
        if pago:
            self._cargar_datos(pago)
        else:
            self.fecha_input.setDate(QDate.currentDate())

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO_DIALOGO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; background: transparent; }}
            QLineEdit, QDateEdit, QComboBox {{
                background-color: {COLOR_FONDO_DIALOGO}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE}; border-radius: 6px;
                padding: 6px 8px; font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{ border: 1px solid {COLOR_ACENTO}; }}
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
        self.socio_combo.currentIndexChanged.connect(self._al_cambiar_socio)

        self.membresia_combo = QComboBox()
        self.membresia_combo.currentIndexChanged.connect(self._al_cambiar_membresia)

        self.monto_input = QLineEdit()
        self.monto_input.setPlaceholderText("Ej: 15000")

        self.metodo_combo = QComboBox()
        for metodo, etiqueta in METODOS_LABELS.items():
            self.metodo_combo.addItem(etiqueta, userData=metodo)

        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDisplayFormat("dd/MM/yyyy")

        self.observaciones_input = QLineEdit()
        self.observaciones_input.setPlaceholderText("Opcional")

        form.addRow("Socio *", self.socio_combo)
        form.addRow("Membresía", self.membresia_combo)
        form.addRow("Monto *", self.monto_input)
        form.addRow("Método de pago *", self.metodo_combo)
        form.addRow("Fecha *", self.fecha_input)
        form.addRow("Observaciones", self.observaciones_input)

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

    def _cargar_socios(self) -> None:
        socios = self._session.query(Socio).filter_by(activo=True).order_by(Socio.apellido, Socio.nombre).all()
        for socio in socios:
            self.socio_combo.addItem(socio.nombre_completo, userData=socio.id)

    def _al_cambiar_socio(self) -> None:
        socio_id = self.socio_combo.currentData()
        self.membresia_combo.blockSignals(True)
        self.membresia_combo.clear()
        self.membresia_combo.addItem("-- Sin asociar --", userData=SIN_MEMBRESIA)

        if socio_id is not None:
            membresias = (
                self._session.query(Membresia)
                .filter_by(socio_id=socio_id)
                .order_by(Membresia.fecha_vencimiento.desc())
                .all()
            )
            for m in membresias:
                etiqueta = f"{m.tipo_membresia.nombre} (vence {m.fecha_vencimiento.strftime('%d/%m/%Y')})"
                self.membresia_combo.addItem(etiqueta, userData=m.id)

            if membresias:
                self.membresia_combo.setCurrentIndex(1)

        self.membresia_combo.blockSignals(False)
        self._al_cambiar_membresia()

    def _al_cambiar_membresia(self) -> None:
        membresia_id = self.membresia_combo.currentData()
        if membresia_id is not None and membresia_id != SIN_MEMBRESIA:
            membresia = self._session.get(Membresia, membresia_id)
            if membresia is not None:
                self.monto_input.setText(str(membresia.tipo_membresia.precio))

    def _cargar_datos(self, pago: Pago) -> None:
        idx_socio = self.socio_combo.findData(pago.socio_id)
        if idx_socio >= 0:
            self.socio_combo.setCurrentIndex(idx_socio)

        if pago.membresia_id is not None:
            idx_membresia = self.membresia_combo.findData(pago.membresia_id)
            if idx_membresia >= 0:
                self.membresia_combo.setCurrentIndex(idx_membresia)

        self.monto_input.setText(str(pago.monto))

        idx_metodo = self.metodo_combo.findData(pago.metodo_pago)
        if idx_metodo >= 0:
            self.metodo_combo.setCurrentIndex(idx_metodo)

        self.fecha_input.setDate(QDate(pago.fecha.year, pago.fecha.month, pago.fecha.day))
        self.observaciones_input.setText(pago.observaciones or "")

    def _guardar(self) -> None:
        socio_id = self.socio_combo.currentData()
        if socio_id is None:
            QMessageBox.warning(self, "Datos incompletos", "Elegí un socio.")
            return

        monto_texto = self.monto_input.text().strip().replace(",", ".")
        try:
            monto = float(monto_texto)
            if monto <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Monto inválido", "El monto debe ser un número mayor a 0.")
            return

        membresia_id = self.membresia_combo.currentData()
        if membresia_id == SIN_MEMBRESIA:
            membresia_id = None

        metodo = self.metodo_combo.currentData()
        qfecha = self.fecha_input.date()
        fecha = datetime(qfecha.year(), qfecha.month(), qfecha.day())
        observaciones = self.observaciones_input.text().strip() or None

        if self._pago is None:
            self._pago = Pago(socio_id=socio_id)
            self._session.add(self._pago)

        self._pago.socio_id = socio_id
        self._pago.membresia_id = membresia_id
        self._pago.monto = monto
        self._pago.metodo_pago = metodo
        self._pago.fecha = fecha
        self._pago.observaciones = observaciones

        self._session.commit()
        self.accept()