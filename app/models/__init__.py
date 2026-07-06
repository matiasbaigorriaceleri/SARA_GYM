"""
Expone todos los modelos para que Base.metadata los reconozca al hacer create_all(),
y para poder importar `from app.models import Socio, Pago, ...` en el resto de la app.

IMPORTANTE: este archivo tiene que importar TODOS los modelos, aunque no se usen
directamente acá, porque SQLAlchemy necesita que las clases estén registradas en el
mismo Base antes de resolver las relaciones declaradas como strings (ej: Mapped["Socio"]).
"""
from app.models.base import Base
from app.models.socio import Socio
from app.models.tipo_membresia import TipoMembresia
from app.models.membresia import Membresia, EstadoMembresia
from app.models.pago import Pago, MetodoPago
from app.models.acceso import Acceso, ResultadoAcceso
from app.models.staff import Staff, RolStaff
from app.models.clase import Clase
from app.models.reserva import Reserva, EstadoReserva
from app.models.setting import Setting
from app.models.license import License

__all__ = [
    "Base",
    "Socio",
    "TipoMembresia",
    "Membresia",
    "EstadoMembresia",
    "Pago",
    "MetodoPago",
    "Acceso",
    "ResultadoAcceso",
    "Staff",
    "RolStaff",
    "Clase",
    "Reserva",
    "EstadoReserva",
    "Setting",
    "License",
]
