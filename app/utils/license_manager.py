"""
Gestor de licencias de SARA GYM.

Mismo esquema conceptual que SARA POS: clave firmada con HMAC-SHA256, formato
GYM-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXX. Validación 100% offline — no depende de
internet, acorde al modelo on-premise.

Estructura de la clave (27 caracteres crudos, antes de agrupar con guiones):
    [1 char tier][8 dígitos fecha vencimiento AAAAMMDD][4 chars serial][14 chars firma HMAC]

La firma se calcula sobre "tier+fecha+serial" con una clave secreta embebida en
la app. Cualquier alteración de un solo caracter invalida la firma.
"""
from __future__ import annotations

import hashlib
import hmac
from datetime import date, datetime
from typing import Optional

# ATENCIÓN: esta clave viaja embebida en el ejecutable de cada cliente porque la
# validación es offline (mismo trade-off ya asumido en SARA POS). No es un secreto
# "irrompible" a nivel criptográfico puro, pero evita que cualquiera arme claves
# válidas a mano. NUNCA cambiarla una vez en producción: invalida todas las
# licencias ya emitidas.
_SECRET_KEY = b"BIMABA-SARA-GYM-2026-LICENSE-SECRET-DO-NOT-SHARE"

LICENSE_PREFIX = "GYM"

TIER_FREE = "FREE"
TIER_GYM_PLUS = "GYM_PLUS"

_TIER_CODES = {"P": TIER_GYM_PLUS}
_TIER_CODES_INVERSE = {v: k for k, v in _TIER_CODES.items()}

_PAYLOAD_LEN = 13    # 1 (tier) + 8 (fecha) + 4 (serial)
_SIGNATURE_LEN = 14  # caracteres hex de la firma


class LicenseError(Exception):
    """Se lanza cuando una clave de licencia es inválida, está corrupta o vencida."""


def _sign(payload: str) -> str:
    digest = hmac.new(_SECRET_KEY, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:_SIGNATURE_LEN].upper()


def _format_key(raw: str) -> str:
    assert len(raw) == _PAYLOAD_LEN + _SIGNATURE_LEN
    groups = [raw[i:i + 4] for i in range(0, 24, 4)] + [raw[24:27]]
    return f"{LICENSE_PREFIX}-" + "-".join(groups)


def _clean_key(license_key: str) -> str:
    """Quita prefijo, guiones y espacios; devuelve el string crudo de 27 caracteres."""
    cleaned = license_key.strip().upper().replace(" ", "")
    if cleaned.startswith(f"{LICENSE_PREFIX}-"):
        cleaned = cleaned[len(LICENSE_PREFIX) + 1:]
    return cleaned.replace("-", "")


def generate_license_key(tier: str, expiration: date, serial: str) -> str:
    """
    Genera una clave de licencia firmada.
    - tier: por ahora solo TIER_GYM_PLUS necesita clave (FREE no lleva clave).
    - expiration: fecha de vencimiento.
    - serial: 4 caracteres (ej: "0001") para identificar la emisión.
    """
    if tier not in _TIER_CODES_INVERSE:
        raise LicenseError(f"Tier desconocido para generar licencia: {tier}")
    if len(serial) != 4:
        raise LicenseError("El serial debe tener exactamente 4 caracteres")

    tier_code = _TIER_CODES_INVERSE[tier]
    fecha_str = expiration.strftime("%Y%m%d")
    payload = f"{tier_code}{fecha_str}{serial.upper()}"

    raw = payload + _sign(payload)
    return _format_key(raw)


def validate_license_key(license_key: str) -> dict:
    """
    Valida una clave y devuelve la información codificada en ella.
    Lanza LicenseError si la clave es inválida, está corrupta o fue alterada.

    Devuelve: {"tier": str, "expiration": date, "serial": str, "expired": bool}
    """
    raw = _clean_key(license_key)

    if len(raw) != _PAYLOAD_LEN + _SIGNATURE_LEN:
        raise LicenseError("Formato de licencia inválido")

    payload, signature = raw[:_PAYLOAD_LEN], raw[_PAYLOAD_LEN:]

    if not hmac.compare_digest(signature, _sign(payload)):
        raise LicenseError("Clave de licencia inválida o adulterada")

    tier_code, fecha_str, serial = payload[0], payload[1:9], payload[9:13]

    if tier_code not in _TIER_CODES:
        raise LicenseError("Tier desconocido en la clave de licencia")

    try:
        expiration = datetime.strptime(fecha_str, "%Y%m%d").date()
    except ValueError as exc:
        raise LicenseError("Fecha de vencimiento inválida en la clave") from exc

    return {
        "tier": _TIER_CODES[tier_code],
        "expiration": expiration,
        "serial": serial,
        "expired": expiration < date.today(),
    }


class LicenseManager:
    """
    Punto único de acceso al estado de la licencia actual del sistema.
    Se instancia pasándole una sesión de SQLAlchemy activa.
    """

    def __init__(self, session):
        self._session = session

    def get_current_tier(self) -> str:
        """
        Devuelve TIER_GYM_PLUS si hay una licencia activa y no vencida,
        TIER_FREE en cualquier otro caso (incluida licencia recién vencida,
        que además se marca como inactiva en la base).
        """
        from app.models import License

        license_row: Optional[License] = (
            self._session.query(License)
            .filter_by(activa=True)
            .order_by(License.id.desc())
            .first()
        )
        if license_row is None:
            return TIER_FREE

        if license_row.fecha_vencimiento and license_row.fecha_vencimiento < date.today():
            license_row.activa = False
            self._session.commit()
            return TIER_FREE

        return license_row.tipo if license_row.tipo == TIER_GYM_PLUS else TIER_FREE

    def activate(self, license_key: str) -> dict:
        """
        Valida una clave y, si es válida y no está vencida, la activa
        (desactivando cualquier licencia previa). Devuelve la info decodificada.
        Lanza LicenseError si la clave no es válida o ya venció.
        """
        from app.models import License

        info = validate_license_key(license_key)
        if info["expired"]:
            raise LicenseError(f"La licencia venció el {info['expiration'].strftime('%d/%m/%Y')}")

        self._session.query(License).update({License.activa: False})

        nueva = License(
            license_key=license_key.strip().upper(),
            tipo=info["tier"],
            fecha_activacion=date.today(),
            fecha_vencimiento=info["expiration"],
            activa=True,
        )
        self._session.add(nueva)
        self._session.commit()
        return info

    def is_gym_plus(self) -> bool:
        return self.get_current_tier() == TIER_GYM_PLUS
