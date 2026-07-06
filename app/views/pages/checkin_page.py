"""
Página de Check-in: búsqueda manual de socios y validación de membresía activa.
Registra cada intento en la tabla Acceso (permitido, denegado por vencimiento,
denegado por suspensión/congelamiento, o no encontrado).
"""
from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)

from app.database.database import get_session
from app.models import Socio, Membresia, EstadoMembresia, Acceso, ResultadoAcceso

COLOR_ACENTO = "#f05133"
COLOR_ACENTO_HOVER = "#d8451f"
COLOR_ACENTO_TEXTO = "#c0451f"
COLOR_TEXTO = "#2a2a2a"
COLOR_TEXTO_MUTED = "#8a8880"
COLOR_VERDE = "#3b8a3e"
COLOR_ROJO = "#c0451f"
COLOR_AMARILLO = "#b8860b"

RESULTADO_LABELS = {
    ResultadoAcceso.PERMITIDO: "Permitido",
    ResultadoAcceso.DENEGADO_VENCIDO: "Denegado (vencido)",
    ResultadoAcceso.DENEGADO_SUSPENDIDO: "Denegado (suspendido)",
    ResultadoAcceso.DENEGADO_NO_ENCONTRADO: "No encontrado",
}
RESULTADO_COLORES = {
    ResultadoAcceso.PERMITIDO: COLOR_VERDE,
    ResultadoAcceso.DENEGADO_VENCIDO: COLOR_ROJO,
    ResultadoAcceso.DENEGADO_SUSPENDIDO: COLOR_AMARILLO,
    ResultadoAcceso.DENEGADO_NO_ENCONTRADO: COLOR_TEXTO_MUTED,
}


class CheckinPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #faf8f4;")
        self._socio_seleccionado_id = None
        self._build_ui()
        self._cargar_historial()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(14)

        titulo = QLabel("Check-in")
        titulo.setStyleSheet(f"color: {COLOR_ACENTO_TEXTO}; font-size: 26px; font-weight: 700;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Búsqueda manual de socios y validación de membresía")
        subtitulo.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px;")
        layout.addWidget(subtitulo)

        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("Buscar por nombre, apellido o DNI...")
        self.busqueda_input.setStyleSheet(
            "QLineEdit { border: 1px solid #e5e2da; border-radius: 6px; padding: 10px 14px; font-size: 15px; }"
        )
        self.busqueda_input.textChanged.connect(self._buscar)
        self.busqueda_input.returnPressed.connect(self._intentar_seleccion_unica)
        layout.addWidget(self.busqueda_input)

        self.resultados_list = QListWidget()
        self.resultados_list.setStyleSheet(
            f"QListWidget {{ border: 1px solid #e5e2da; border-radius: 8px; background-color: white;"
            f" color: {COLOR_TEXTO}; font-size: 13px; }}"
            "QListWidget::item { padding: 8px 12px; }"
            "QListWidget::item:selected { background-color: #f1eee6; }"
        )
        self.resultados_list.setMaximumHeight(140)
        self.resultados_list.itemClicked.connect(self._seleccionar_desde_lista)
        self.resultados_list.hide()
        layout.addWidget(self.resultados_list)

        self.card = self._crear_card()
        layout.addWidget(self.card)

        self.mensaje_resultado = QLabel("")
        self.mensaje_resultado.setAlignment(Qt.AlignCenter)
        self.mensaje_resultado.hide()
        layout.addWidget(self.mensaje_resultado)

        historial_label = QLabel("Últimos accesos")
        historial_label.setStyleSheet(
            f"color: {COLOR_TEXTO_MUTED}; font-size: 12px; font-weight: 500; margin-top: 8px;"
        )
        layout.addWidget(historial_label)

        self.historial_tabla = QTableWidget(0, 3)
        self.historial_tabla.setHorizontalHeaderLabels(["Socio", "Resultado", "Fecha y hora"])
        self.historial_tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.historial_tabla.verticalHeader().setVisible(False)
        self.historial_tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.historial_tabla.setSelectionMode(QTableWidget.NoSelection)
        self.historial_tabla.setStyleSheet(
            "QTableWidget { border: 1px solid #e5e2da; border-radius: 8px; background-color: white; }"
            "QHeaderView::section { background-color: #f1eee6; color: #8a8880; font-size: 12px;"
            " padding: 8px; border: none; }"
        )
        layout.addWidget(self.historial_tabla, stretch=1)

        self.busqueda_input.setFocus()

    def _crear_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #e5e2da; border-radius: 8px; }"
        )
        card.hide()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(4)

        self.card_nombre = QLabel("")
        self.card_nombre.setStyleSheet(f"color: {COLOR_TEXTO}; font-size: 18px; font-weight: 700;")
        card_layout.addWidget(self.card_nombre)

        self.card_estado = QLabel("")
        self.card_estado.setStyleSheet("font-size: 13px; font-weight: 500;")
        card_layout.addWidget(self.card_estado)

        self.card_vencimiento = QLabel("")
        self.card_vencimiento.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 12px;")
        card_layout.addWidget(self.card_vencimiento)

        self.boton_registrar = QPushButton("Registrar acceso")
        self.boton_registrar.setCursor(Qt.PointingHandCursor)
        self.boton_registrar.setFlat(True)
        self.boton_registrar.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_ACENTO}; color: white; border: none;"
            f" border-radius: 6px; padding: 10px; font-weight: 500; font-size: 14px; margin-top: 8px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_ACENTO_HOVER}; }}"
        )
        self.boton_registrar.clicked.connect(self._registrar_acceso)
        card_layout.addWidget(self.boton_registrar)

        return card

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._cargar_historial()

    def _buscar(self) -> None:
        texto = self.busqueda_input.text().strip()
        self.mensaje_resultado.hide()
        self.card.hide()
        self.resultados_list.clear()
        self._socio_seleccionado_id = None

        if not texto:
            self.resultados_list.hide()
            return

        session = get_session()
        try:
            filtro = texto.lower()
            socios = session.query(Socio).filter_by(activo=True).order_by(Socio.apellido, Socio.nombre).all()
            coincidencias = [
                s for s in socios
                if filtro in s.nombre.lower() or filtro in s.apellido.lower() or (s.dni and filtro in s.dni.lower())
            ]

            if not coincidencias:
                self.resultados_list.hide()
                self.card_nombre.setText(f"\"{texto}\"")
                self.card_estado.setText("No se encontraron coincidencias")
                self.card_estado.setStyleSheet(f"color: {COLOR_TEXTO_MUTED}; font-size: 13px; font-weight: 500;")
                self.card_vencimiento.setText("")
                self.card.show()
                return

            for socio in coincidencias:
                item = QListWidgetItem(f"{socio.nombre_completo} — DNI {socio.dni or 's/d'}")
                item.setData(Qt.UserRole, socio.id)
                self.resultados_list.addItem(item)

            self.resultados_list.show()
        finally:
            session.close()

    def _intentar_seleccion_unica(self) -> None:
        if self.resultados_list.count() == 1:
            self._seleccionar_desde_lista(self.resultados_list.item(0))

    def _seleccionar_desde_lista(self, item: QListWidgetItem) -> None:
        socio_id = item.data(Qt.UserRole)
        self._socio_seleccionado_id = socio_id
        self.resultados_list.hide()
        self._mostrar_card(socio_id)

    def _mostrar_card(self, socio_id: int) -> None:
        session = get_session()
        try:
            socio = session.get(Socio, socio_id)
            if socio is None:
                return

            self.card_nombre.setText(socio.nombre_completo)

            membresia = (
                session.query(Membresia)
                .filter_by(socio_id=socio.id)
                .order_by(Membresia.fecha_vencimiento.desc())
                .first()
            )

            if membresia is None:
                self.card_estado.setText("Sin membresía asignada")
                self.card_estado.setStyleSheet(f"color: {COLOR_ROJO}; font-size: 13px; font-weight: 500;")
                self.card_vencimiento.setText("")
            elif membresia.estado == EstadoMembresia.ACTIVA and membresia.fecha_vencimiento >= date.today():
                self.card_estado.setText(f"Activa — {membresia.tipo_membresia.nombre}")
                self.card_estado.setStyleSheet(f"color: {COLOR_VERDE}; font-size: 13px; font-weight: 500;")
                self.card_vencimiento.setText(f"Vence: {membresia.fecha_vencimiento.strftime('%d/%m/%Y')}")
            elif membresia.estado in (EstadoMembresia.SUSPENDIDA, EstadoMembresia.CONGELADA):
                self.card_estado.setText(f"{membresia.estado.value.capitalize()} — {membresia.tipo_membresia.nombre}")
                self.card_estado.setStyleSheet(f"color: {COLOR_AMARILLO}; font-size: 13px; font-weight: 500;")
                self.card_vencimiento.setText(f"Vence: {membresia.fecha_vencimiento.strftime('%d/%m/%Y')}")
            else:
                self.card_estado.setText(f"Vencida — {membresia.tipo_membresia.nombre}")
                self.card_estado.setStyleSheet(f"color: {COLOR_ROJO}; font-size: 13px; font-weight: 500;")
                self.card_vencimiento.setText(f"Venció: {membresia.fecha_vencimiento.strftime('%d/%m/%Y')}")

            self.card.show()
        finally:
            session.close()

    def _registrar_acceso(self) -> None:
        session = get_session()
        try:
            socio_id = self._socio_seleccionado_id
            socio = session.get(Socio, socio_id) if socio_id else None

            if socio is None:
                resultado = ResultadoAcceso.DENEGADO_NO_ENCONTRADO
            else:
                membresia = (
                    session.query(Membresia)
                    .filter_by(socio_id=socio.id)
                    .order_by(Membresia.fecha_vencimiento.desc())
                    .first()
                )
                if membresia is None:
                    resultado = ResultadoAcceso.DENEGADO_VENCIDO
                elif membresia.estado in (EstadoMembresia.SUSPENDIDA, EstadoMembresia.CONGELADA):
                    resultado = ResultadoAcceso.DENEGADO_SUSPENDIDO
                elif membresia.estado == EstadoMembresia.ACTIVA and membresia.fecha_vencimiento >= date.today():
                    resultado = ResultadoAcceso.PERMITIDO
                else:
                    resultado = ResultadoAcceso.DENEGADO_VENCIDO

            acceso = Acceso(socio_id=socio_id, resultado=resultado)
            session.add(acceso)
            session.commit()

            self._mostrar_resultado(resultado)
            self._cargar_historial()
        finally:
            session.close()

    def _mostrar_resultado(self, resultado: ResultadoAcceso) -> None:
        color = RESULTADO_COLORES[resultado]
        if resultado == ResultadoAcceso.PERMITIDO:
            texto = "✓ ACCESO PERMITIDO"
        elif resultado == ResultadoAcceso.DENEGADO_VENCIDO:
            texto = "✗ ACCESO DENEGADO — Membresía vencida"
        elif resultado == ResultadoAcceso.DENEGADO_SUSPENDIDO:
            texto = "✗ ACCESO DENEGADO — Membresía suspendida/congelada"
        else:
            texto = "✗ SOCIO NO ENCONTRADO"

        self.mensaje_resultado.setText(texto)
        self.mensaje_resultado.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: 700; padding: 10px;")
        self.mensaje_resultado.show()

    def _cargar_historial(self) -> None:
        session = get_session()
        try:
            accesos = (
                session.query(Acceso)
                .order_by(Acceso.fecha_hora.desc())
                .limit(20)
                .all()
            )
            self.historial_tabla.setRowCount(len(accesos))

            for fila, acceso in enumerate(accesos):
                nombre_socio = acceso.socio.nombre_completo if acceso.socio else "(no encontrado)"
                item_socio = QTableWidgetItem(nombre_socio)
                item_socio.setForeground(QColor(COLOR_TEXTO))

                item_resultado = QTableWidgetItem(RESULTADO_LABELS[acceso.resultado])
                item_resultado.setForeground(QColor(RESULTADO_COLORES[acceso.resultado]))

                item_fecha = QTableWidgetItem(acceso.fecha_hora.strftime("%d/%m/%Y %H:%M"))
                item_fecha.setForeground(QColor(COLOR_TEXTO))

                self.historial_tabla.setItem(fila, 0, item_socio)
                self.historial_tabla.setItem(fila, 1, item_resultado)
                self.historial_tabla.setItem(fila, 2, item_fecha)

            self.historial_tabla.resizeRowsToContents()
        finally:
            session.close()