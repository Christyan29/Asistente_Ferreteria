"""
Modelos ORM de SQLAlchemy para la base de datos.
Define las tablas de Producto y Categoría.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CategoriaModel(Base):
    """Modelo ORM para la tabla de categorías"""
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relación con productos
    productos = relationship("ProductoModel", back_populates="categoria", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CategoriaModel(id={self.id}, nombre='{self.nombre}')>"


class ProductoModel(Base):
    """Modelo ORM para la tabla de productos"""
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, index=True, nullable=True)
    nombre = Column(String(200), nullable=False, index=True)
    descripcion = Column(Text, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    stock_minimo = Column(Integer, default=0, nullable=False)
    unidad_medida = Column(String(20), default="unidad", nullable=False)
    marca = Column(String(100), nullable=True)
    ubicacion = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Foreign key a categoría
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)

    # Relación con categoría
    categoria = relationship("CategoriaModel", back_populates="productos")

    def __repr__(self):
        return f"<ProductoModel(id={self.id}, codigo='{self.codigo}', nombre='{self.nombre}', stock={self.stock})>"
