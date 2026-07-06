"""
Herramienta interna para generar claves de licencia SARA GYM+.
Uso exclusivo de BIMABA — NO se distribuye a clientes.

Ejecutar parado en la raíz del repo:
    python tools/generate_license.py
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.license_manager import generate_license_key, TIER_GYM_PLUS  # noqa: E402


def main() -> None:
    print("=== Generador de licencias SARA GYM+ ===\n")

    serial = input("Serial de 4 caracteres (ej: 0001): ").strip().upper()
    while len(serial) != 4:
        print("El serial debe tener exactamente 4 caracteres.")
        serial = input("Serial de 4 caracteres (ej: 0001): ").strip().upper()

    meses_input = input("Duración en meses (default 12): ").strip()
    meses = int(meses_input) if meses_input else 12

    expiration = date.today() + timedelta(days=meses * 30)

    key = generate_license_key(tier=TIER_GYM_PLUS, expiration=expiration, serial=serial)

    print(f"\nClave generada:\n\n  {key}\n")
    print("Tier: GYM_PLUS")
    print(f"Vence: {expiration.strftime('%d/%m/%Y')}")


if __name__ == "__main__":
    main()
