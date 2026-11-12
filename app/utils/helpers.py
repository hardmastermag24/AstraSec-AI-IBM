"""
AstraSec AI — Utilidades compartidas.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env() -> None:
    """Carga .env si existe, sin sobreescribir variables ya definidas."""
    try:
        from dotenv import load_dotenv  # noqa: PLC0415
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
    except ImportError:
        pass  # python-dotenv no disponible; se usan variables del sistema


def get_int_env(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default
