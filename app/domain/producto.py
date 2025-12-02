"""
Entidad de dominio: Producto
Representa un producto en el inventario de la ferretería.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from decimal import Decimal


@dataclass
class Producto:
    """
    Entidad de dominio para productos del inventario.

    Attributes:
        id: Identificador único del producto
        codigo: Código SKU o identificador del producto
        nombre: Nombre del producto
        descripcion: Descripción detallada
        precio: Precio unitario del producto
        stock: Cantidad disponible en inventario
        stock_minimo: Nivel mínimo de stock antes de alertar
        unidad_medida: Unidad de medida (ej: "unidad", "metro", "litro")
        categoria_id: ID de la categoría a la que pertenece
        categoria_nombre: Nombre de la categoría (para consultas)
        marca: Marca del producto
        ubicacion: Ubicación física en la ferretería
        activo: Indica si el producto está activo
        created_at: Fecha de creación
        updated_at: Fecha de última actualización
    """
    nombre: str
    precio: Decimal
    stock: int
    codigo: Optional[str] = None
    descripcion: Optional[str] = None
    stock_minimo: int = 0
    unidad_medida: str = "unidad"
    categoria_id: Optional[int] = None
    categoria_nombre: Optional[str] = None
    marca: Optional[str] = None
    ubicacion: Optional[str] = None
    activo: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del producto no puede estar vacío")

        if self.precio < 0:
            raise ValueError("El precio no puede ser negativo")

        if self.stock < 0:
            raise ValueError("El stock no puede ser negativo")

        if self.stock_minimo < 0:
            raise ValueError("El stock mínimo no puede ser negativo")

        # Normalizar campos de texto
        self.nombre = self.nombre.strip()
        if self.codigo:
            self.codigo = self.codigo.strip().upper()
        if self.marca:
            self.marca = self.marca.strip()

    def __str__(self) -> str:
        return f"{self.nombre} - ${self.precio} ({self.stock} {self.unidad_medida})"

    def __repr__(self) -> str:
        return f"Producto(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}', stock={self.stock})"

    @property
    def tiene_stock(self) -> bool:
        """Verifica si hay stock disponible"""
        return self.stock > 0

    @property
    def stock_bajo(self) -> bool:
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.stock_minimo

    @property
    def precio_formateado(self) -> str:
        """Retorna el precio formateado como string"""
        return f"${self.precio:.2f}"

    def actualizar_stock(self, cantidad: int) -> None:
        """
        Actualiza el stock del producto.

        Args:
            cantidad: Cantidad a agregar (positivo) o quitar (negativo)

        Raises:
            ValueError: Si la operación resulta en stock negativo
        """
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            raise ValueError(f"Stock insuficiente. Stock actual: {self.stock}, cantidad solicitada: {abs(cantidad)}")
        self.stock = nuevo_stock

    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario"""
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": float(self.precio),
            "stock": self.stock,
            "stock_minimo": self.stock_minimo,
            "unidad_medida": self.unidad_medida,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria_nombre,
            "marca": self.marca,
            "ubicacion": self.ubicacion,
            "activo": self.activo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tiene_stock": self.tiene_stock,
            "stock_bajo": self.stock_bajo,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Producto':
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get("id"),
            codigo=data.get("codigo"),
            nombre=data["nombre"],
            descripcion=data.get("descripcion"),
            precio=Decimal(str(data["precio"])),
            stock=data.get("stock", 0),
            stock_minimo=data.get("stock_minimo", 0),
            unidad_medida=data.get("unidad_medida", "unidad"),
            categoria_id=data.get("categoria_id"),
            categoria_nombre=data.get("categoria_nombre"),
            marca=data.get("marca"),
            ubicacion=data.get("ubicacion"),
            activo=data.get("activo", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
