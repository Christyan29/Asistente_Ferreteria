"""
Modelos ORM para el sistema de proveedores y pedidos.
SOLO AGREGA TABLAS NUEVAS - No modifica tablas existentes.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Numeric, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.models.producto import Base


class ProveedorModel(Base):
    """Tabla: proveedores - Catálogo de proveedores de la ferretería"""
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(150), nullable=False, index=True)
    contacto = Column(String(100), nullable=True)   # nombre del contacto
    telefono = Column(String(30), nullable=True)
    email = Column(String(120), nullable=True)
    notas = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relaciones
    producto_proveedores = relationship(
        "ProductoProveedorModel",
        back_populates="proveedor",
        cascade="all, delete-orphan"
    )
    pedidos = relationship(
        "PedidoProveedorModel",
        back_populates="proveedor"
    )

    def __repr__(self):
        return f"<ProveedorModel(id={self.id}, nombre='{self.nombre}')>"


class ProductoProveedorModel(Base):
    """Tabla: producto_proveedor - Relación muchos a muchos entre productos y proveedores"""
    __tablename__ = "producto_proveedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    proveedor_id = Column(
        Integer,
        ForeignKey("proveedores.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    es_principal = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    proveedor = relationship("ProveedorModel", back_populates="producto_proveedores")

    def __repr__(self):
        return (
            f"<ProductoProveedorModel(producto_id={self.producto_id}, "
            f"proveedor_id={self.proveedor_id}, principal={self.es_principal})>"
        )


class PedidoProveedorModel(Base):
    """Tabla: pedidos_proveedor - Registro de pedidos generados al proveedor"""
    __tablename__ = "pedidos_proveedor"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proveedor_id = Column(
        Integer,
        ForeignKey("proveedores.id", ondelete="SET NULL"),
        nullable=True,   # nullable por si se eliminó el proveedor
        index=True
    )
    proveedor_nombre_snapshot = Column(String(150), nullable=True)  # copia del nombre al momento del pedido
    estado = Column(String(20), default="pendiente", nullable=False)  # pendiente | aprobado | enviado | cancelado
    notas = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)   # usuario autenticado
    fecha_pedido = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relaciones
    proveedor = relationship("ProveedorModel", back_populates="pedidos")
    detalles = relationship(
        "DetallePedidoModel",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<PedidoProveedorModel(id={self.id}, estado='{self.estado}')>"


class DetallePedidoModel(Base):
    """Tabla: detalle_pedido - Líneas de productos dentro de un pedido"""
    __tablename__ = "detalle_pedido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(
        Integer,
        ForeignKey("pedidos_proveedor.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    producto_id = Column(
        Integer,
        ForeignKey("productos.id", ondelete="SET NULL"),
        nullable=True
    )
    producto_nombre_snapshot = Column(String(200), nullable=False)   # copia del nombre al momento del pedido
    cantidad_solicitada = Column(Integer, nullable=False)
    precio_unitario_snapshot = Column(Numeric(10, 2), nullable=True)  # precio al momento del pedido
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relaciones
    pedido = relationship("PedidoProveedorModel", back_populates="detalles")

    def __repr__(self):
        return (
            f"<DetallePedidoModel(pedido_id={self.pedido_id}, "
            f"producto='{self.producto_nombre_snapshot}', "
            f"cantidad={self.cantidad_solicitada})>"
        )
