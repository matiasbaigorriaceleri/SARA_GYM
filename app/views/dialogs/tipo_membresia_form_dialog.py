"""
Diálogo de alta/edición de TipoMembresia (plan: mensual, trimestral, etc.)
Si `tipo` es None, es un alta nueva; si se pasa uno existente, edita sus datos.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox,
    QPushButton, QHBoxLayout, QMessageBox,
)

from app.models import TipoMembresia

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_FONDO_DIALOGO = "#ffffff"
COLOR_TEXTO = "#2a2a2a"
COLOR_BORDE = "#cfcac0"


class TipoMembresiaFormDialog(QDialog):
    def __init__(self, session, tipo: Optional[TipoMembresia] = None, parent=None):
        super().__init__(parent)
        self._session = session
        self._tipo = tipo
        self.setWindowTitle("Editar plan" if tipo else "Nuevo plan")
        self.setMinimumWidth(380)
        self._aplicar_estilos()
        self._build_ui()
        if tipo:
            self._cargar_datos(tipo)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(f"""
            QDialog {{ background-color: {COLOR_FONDO_DIALOGO}; }}
            QLabel {{ color: {COLOR_TEXTO}; font-size: 13px; background: transparent; }}
            QLineEdit {{
                background-color: {COLOR_FONDO_DIALOGO}; color: {COLOR_TEXTO};
                border: 1px solid {COLOR_BORDE}; border-radius: 6px;
                padding: 6px 8px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {COLOR_ACENTO}; }}
            QCheckBox {{ color: {COLOR_TEXTO}; font-size: 13px; }}
        """)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Mensual, Trimestral, Clases sueltas")

        self.duracion_input = QLineEdit()
        self.duracion_input.setPlaceholderText("Ej: 30")

        self.precio_input = QLineEdit()
        self.precio_input.setPlaceholderText("Ej: 15000")

        self.clases_incluidas_input = QLineEdit()
        self.clases_incluidas_input.setPlaceholderText("Vacío = ilimitadas")

        self.activo_check = QCheckBox("Plan activo (disponible para asignar)")
        self.activo_check.setChecked(True)

        form.addRow("Nombre *", self.nombre_input)
        form.addRow("Duración (días) *", self.duracion_input)
        form.addRow("Precio *", self.precio_input)
        form.addRow("Clases incluidas", self.clases_incluidas_input)
        form.addRow("", self.activo_check)

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

    def _cargar_datos(self, tipo: TipoMembresia) -> None:
        self.nombre_input.setText(tipo.nombre)
        self.duracion_input.setText(str(tipo.duracion_dias))
        self.precio_input.setText(str(tipo.precio))
        self.clases_incluidas_input.setText(
            str(tipo.clases_incluidas) if tipo.clases_incluidas is not None else ""
        )
        self.activo_check.setChecked(tipo.activo)

    def _guardar(self) -> None:
        nombre = self.nombre_input.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Datos incompletos", "El nombre del plan es obligatorio.")
            return

        duracion_texto = self.duracion_input.text().strip()
        if not duracion_texto.isdigit() or int(duracion_texto) <= 0:
            QMessageBox.warning(self, "Duración inválida", "La duración debe ser un número entero mayor a 0.")
            return
        duracion_dias = int(duracion_texto)

        precio_texto = self.precio_input.text().strip().replace(",", ".")
        try:
            precio = float(precio_texto)
            if precio < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Precio inválido", "El precio debe ser un número válido mayor o igual a 0.")
            return

        clases_texto = self.clases_incluidas_input.text().strip()
        clases_incluidas = None
        if clases_texto:
            if not clases_texto.isdigit() or int(clases_texto) <= 0:
                QMessageBox.warning(
                    self, "Clases inválidas",
                    "Las clases incluidas deben ser un número entero mayor a 0, o dejarse vacío para ilimitadas.",
                )
                return
            clases_incluidas = int(clases_texto)

        if self._tipo is None:
            self._tipo = TipoMembresia(nombre=nombre)
            self._session.add(self._tipo)

        self._tipo.nombre = nombre
        self._tipo.duracion_dias = duracion_dias
        self._tipo.precio = precio
        self._tipo.clases_incluidas = clases_incluidas
        self._tipo.activo = self.activo_check.isChecked()

        self._session.commit()
        self.accept()