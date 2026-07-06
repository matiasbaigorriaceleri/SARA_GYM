"""
Diálogo de alta/edición de Socio.
Muestra siempre una sección de plan de membresía: en altas nuevas permite
asignar una membresía inicial opcional; al editar, muestra el plan actual del
socio (si tiene uno activo) y permite cambiarlo, conservando su fecha de inicio
original y recalculando el vencimiento según la nueva duración.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QTextEdit,
    QComboBox, QPushButton, QHBoxLayout, QMessageBox, QFrame, QLabel,
)

from app.models import Socio, TipoMembresia, Membresia, EstadoMembresia

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_FONDO_DIALOGO = "#ffffff"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_BORDE = "#cfcac0"

SIN_ASIGNAR = -1


class SocioFormDialog(QDialog):
    def __init__(self, session, socio: Optional[Socio] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._socio = socio
        self._es_alta = socio is None

        self._membresia_actual: Optional[Membresia] = None
        if socio is not None:
            self._membresia_actual = (
                session.query(Membresia)
                .filter_by(socio_id=socio.id, estado=EstadoMembresia.ACTIVA)
                .order_by(Membresia.fecha_vencimiento.desc())
                .first()
            )

        self.setWindowTitle("Editar socio" if socio else "Nuevo socio")
        self.setMinimumWidth(420)
        self._aplicar_estilos()
        self._build_ui()
        if socio:
            self._cargar_datos(socio)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO_DIALOGO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; background: transparent; }}
            QLineEdit, QDateEdit, QTextEdit, QComboBox {{
                background-color: {COLOR_FONDO_DIALOGO}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE}; border-radius: 6px;
                padding: 6px 8px; font-size: 13px;
            }}
            QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus {{
                border: 1px solid {COLOR_ACENTO};
            }}
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

        self.nombre_input = QLineEdit()
        self.apellido_input = QLineEdit()
        self.dni_input = QLineEdit()
        self.email_input = QLineEdit()
        self.telefono_input = QLineEdit()
        self.direccion_input = QLineEdit()

        self.fecha_nacimiento_input = QDateEdit()
        self.fecha_nacimiento_input.setCalendarPopup(True)
        self.fecha_nacimiento_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_nacimiento_input.setDate(QDate(2000, 1, 1))

        self.contacto_nombre_input = QLineEdit()
        self.contacto_telefono_input = QLineEdit()

        self.observaciones_input = QTextEdit()
        self.observaciones_input.setFixedHeight(60)

        form.addRow("Nombre *", self.nombre_input)
        form.addRow("Apellido *", self.apellido_input)
        form.addRow("DNI", self.dni_input)
        form.addRow("Email", self.email_input)
        form.addRow("Teléfono", self.telefono_input)
        form.addRow("Dirección", self.direccion_input)
        form.addRow("Fecha de nacimiento", self.fecha_nacimiento_input)
        form.addRow("Contacto de emergencia", self.contacto_nombre_input)
        form.addRow("Tel. de emergencia", self.contacto_telefono_input)
        form.addRow("Observaciones", self.observaciones_input)

        layout.addLayout(form)

        linea = QFrame()
        linea.setFrameShape(QFrame.HLine)
        linea.setStyleSheet(f"background-color: {COLOR_BORDE}; max-height: 1px; border: none;")
        layout.addWidget(linea)

        texto_seccion = "Plan de membresía" if not self._es_alta else "Asignar membresía (opcional)"
        subtitulo = QLabel(texto_seccion)
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 12px; font-weight: 500;")
        layout.addWidget(subtitulo)

        form_membresia = QFormLayout()
        form_membresia.setSpacing(10)

        self.plan_combo = QComboBox()
        self.plan_combo.addItem("-- Sin asignar --", userData=SIN_ASIGNAR)
        tipos = (
            self._session.query(TipoMembresia)
            .filter_by(activo=True)
            .order_by(TipoMembresia.nombre)
            .all()
        )
        for tipo in tipos:
            self.plan_combo.addItem(f"{tipo.nombre} ({tipo.duracion_dias} días)", userData=tipo.id)

        if self._membresia_actual is not None:
            idx_actual = self.plan_combo.findData(self._membresia_actual.tipo_membresia_id)
            if idx_actual >= 0:
                self.plan_combo.setCurrentIndex(idx_actual)

        form_membresia.addRow("Plan", self.plan_combo)
        layout.addLayout(form_membresia)

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

    def _cargar_datos(self, socio: Socio) -> None:
        self.nombre_input.setText(socio.nombre)
        self.apellido_input.setText(socio.apellido)
        self.dni_input.setText(socio.dni or "")
        self.email_input.setText(socio.email or "")
        self.telefono_input.setText(socio.telefono or "")
        self.direccion_input.setText(socio.direccion or "")
        if socio.fecha_nacimiento:
            f = socio.fecha_nacimiento
            self.fecha_nacimiento_input.setDate(QDate(f.year, f.month, f.day))
        self.contacto_nombre_input.setText(socio.contacto_emergencia_nombre or "")
        self.contacto_telefono_input.setText(socio.contacto_emergencia_telefono or "")
        self.observaciones_input.setPlainText(socio.observaciones or "")

    def _guardar(self) -> None:
        nombre = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()

        if not nombre or not apellido:
            QMessageBox.warning(self, "Datos incompletos", "Nombre y apellido son obligatorios.")
            return

        dni = self.dni_input.text().strip() or None

        if dni:
            query = self._session.query(Socio).filter(Socio.dni == dni)
            if self._socio is not None:
                query = query.filter(Socio.id != self._socio.id)
            if query.first() is not None:
                QMessageBox.warning(self, "DNI duplicado", "Ya existe otro socio registrado con ese DNI.")
                return

        qdate = self.fecha_nacimiento_input.date()
        fecha_nacimiento = date(qdate.year(), qdate.month(), qdate.day())

        if self._socio is None:
            self._socio = Socio(nombre=nombre, apellido=apellido)
            self._session.add(self._socio)

        self._socio.nombre = nombre
        self._socio.apellido = apellido
        self._socio.dni = dni
        self._socio.email = self.email_input.text().strip() or None
        self._socio.telefono = self.telefono_input.text().strip() or None
        self._socio.direccion = self.direccion_input.text().strip() or None
        self._socio.fecha_nacimiento = fecha_nacimiento
        self._socio.contacto_emergencia_nombre = self.contacto_nombre_input.text().strip() or None
        self._socio.contacto_emergencia_telefono = self.contacto_telefono_input.text().strip() or None
        self._socio.observaciones = self.observaciones_input.toPlainText().strip() or None

        tipo_id = self.plan_combo.currentData()
        if tipo_id is not None and tipo_id != SIN_ASIGNAR:
            self._session.flush()
            tipo = self._session.get(TipoMembresia, tipo_id)

            if self._membresia_actual is not None:
                self._membresia_actual.tipo_membresia_id = tipo.id
                self._membresia_actual.fecha_vencimiento = (
                    self._membresia_actual.fecha_inicio + timedelta(days=tipo.duracion_dias)
                )
            else:
                fecha_inicio = date.today()
                fecha_vencimiento = fecha_inicio + timedelta(days=tipo.duracion_dias)
                membresia = Membresia(
                    socio_id=self._socio.id,
                    tipo_membresia_id=tipo.id,
                    fecha_inicio=fecha_inicio,
                    fecha_vencimiento=fecha_vencimiento,
                    estado=EstadoMembresia.ACTIVA,
                )
                self._session.add(membresia)

        self._session.commit()
        self.accept()