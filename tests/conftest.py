"""Configuracion comun de las pruebas: rutas de importacion y acceso a la base si existe."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="session")
def dataset():
    import seed

    return seed.generate_dataset()


@pytest.fixture(scope="session")
def db_available() -> bool:
    """True si hay una base cargada a la que conectarse; las pruebas que la necesitan se saltean si no."""
    try:
        from telemetry_agent.db import connect_admin

        with connect_admin() as conn:
            conn.execute("select count(*) from equipos").fetchone()
        return True
    except Exception:
        return False
