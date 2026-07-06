"""
Notificador de leads a BIMABA para SARA GYM.

Mismo patrón que SARA POS: cuando un cliente completa el registro obligatorio
del wizard de configuración, se dispara un email a soportesara@bimaba.com con
sus datos. Corre en un hilo aparte (no bloquea la UI) y falla en silencio si
hay cualquier problema — el wizard NUNCA debe mostrar un error por esto.
"""
from __future__ import annotations

import smtplib
import threading
from email.mime.text import MIMEText

# Mismas credenciales que SARA POS — la casilla de soporte es la misma para
# ambos productos, remitente y destinatario son soportesara@bimaba.com.
_SMTP_HOST = "c2781833.ferozo.com"
_SMTP_PORT = 465  # SSL
_SMTP_USER = "soportesara@bimaba.com"
_SMTP_PASSWORD = "Saar4POs2026/@*"
_DESTINATARIO = "soportesara@bimaba.com"
_SMTP_TIMEOUT = 10  # segundos — evita que el hilo quede colgado si no hay red

# Como SARA POS y SARA GYM comparten la misma casilla de leads, este prefijo en
# el asunto es lo único que permite distinguir de qué producto viene cada uno.
_PRODUCTO = "SARA GYM"


def _enviar_email(asunto: str, cuerpo: str) -> None:
    """Envía el email de forma sincrónica. Pensado para correr dentro de un hilo."""
    try:
        msg = MIMEText(cuerpo, "plain", "utf-8")
        msg["Subject"] = asunto
        msg["From"] = _SMTP_USER
        msg["To"] = _DESTINATARIO

        with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, timeout=_SMTP_TIMEOUT) as server:
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_SMTP_USER, [_DESTINATARIO], msg.as_string())
    except Exception:
        # Silencio a propósito: el wizard nunca debe mostrarle un error al
        # usuario por esto. Mismo criterio que en SARA POS.
        pass


def notify_new_lead(
    nombre: str,
    apellido: str,
    email: str,
    telefono: str = "",
    pais: str = "",
    ciudad: str = "",
    localidad: str = "",
) -> None:
    """
    Dispara el envío del email de lead en un hilo aparte (no bloqueante).
    Se llama una única vez, al completar el paso de registro obligatorio del wizard.
    """
    asunto = f"nuevo_cliente_gym — {nombre} {apellido}"
    cuerpo = (
        f"Nuevo registro en {_PRODUCTO}\n\n"
        f"Nombre: {nombre}\n"
        f"Apellido: {apellido}\n"
        f"Email: {email}\n"
        f"Teléfono: {telefono}\n"
        f"País: {pais}\n"
        f"Ciudad: {ciudad}\n"
        f"Localidad: {localidad}\n"
    )

    thread = threading.Thread(target=_enviar_email, args=(asunto, cuerpo), daemon=True)
    thread.start()