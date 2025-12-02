"""
Entidad de dominio: Categoría
Representa una categoría de productos en la ferretería.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Categoria:
    """
    Entidad de dominio para categorías de productos.

    Attributes:
        id: Identificador único de la categoría
        nombre: Nombre de la categoría (ej: "Herramientas", "Pinturas")
        descripcion: Descripción detallada de la categoría
        activo: Indica si la categoría está activa
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    nombre: str
    descripcion: Optional[str] = None
    activo: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")

        # Normalizar el nombre
        self.nombre = self.nombre.strip().title()

    def __str__(self) -> str:
        return f"Categoría: {self.nombre}"

    def __repr__(self) -> str:
        return f"Categoria(id={self.id}, nombre='{self.nombre}', activo={self.activo})"

    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario"""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Categoria':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get("id"),
            nombre=data["nombre"],
            descripcion=data.get("descripcion"),
            activo=data.get("activo", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
