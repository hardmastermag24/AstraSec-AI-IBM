"""
AstraSec AI — Gestión del laboratorio activo.

Responsabilidades:
- Almacenar y recuperar nombre, descripción y metadatos del laboratorio.
- No conecta redes ni ejecuta código externo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Laboratory:
    name: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    analyst: str = ""
    scope: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "Laboratory":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds")),
            analyst=data.get("analyst", ""),
            scope=data.get("scope", ""),
        )


def create_laboratory(name: str, description: str, analyst: str = "", scope: str = "") -> Laboratory:
    """Crea un nuevo laboratorio validando los campos obligatorios."""
    name = name.strip()
    description = description.strip()
    if not name:
        raise ValueError("El nombre del laboratorio no puede estar vacío.")
    if not description:
        raise ValueError("La descripción del laboratorio no puede estar vacía.")
    return Laboratory(name=name, description=description, analyst=analyst.strip(), scope=scope.strip())
