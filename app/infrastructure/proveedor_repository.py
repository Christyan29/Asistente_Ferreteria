"""
Repositorio para operaciones CRUD de proveedores.
Maneja también la relación producto-proveedor.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from app.infrastructure.models.proveedor import (
    ProveedorModel, ProductoProveedorModel
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entidad de dominio ligera (sin ORM, sin dependencias circulares)
# ---------------------------------------------------------------------------

class Proveedor:
    """Entidad de dominio para Proveedor"""
    def __init__(
        self,
        id: Optional[int] = None,
        nombre: str = "",
        contacto: Optional[str] = None,
        telefono: Optional[str] = None,
        email: Optional[str] = None,
        notas: Optional[str] = None,
        activo: bool = True,
    ):
        self.id = id
        self.nombre = nombre
        self.contacto = contacto
        self.telefono = telefono
        self.email = email
        self.notas = notas
        self.activo = activo

    def __repr__(self):
        return f"<Proveedor(id={self.id}, nombre='{self.nombre}')>"


# ---------------------------------------------------------------------------
# Repositorio de Proveedores
# ---------------------------------------------------------------------------

class ProveedorRepository:
    """CRUD completo de proveedores"""

    def _get_session(self) -> Session:
        from app.infrastructure.database import get_session
        return get_session()

    # ---- Conversión modelo ↔ entidad ----

    @staticmethod
    def _to_entity(model: ProveedorModel) -> Proveedor:
        return Proveedor(
            id=model.id,
            nombre=model.nombre,
            contacto=model.contacto,
            telefono=model.telefono,
            email=model.email,
            notas=model.notas,
            activo=model.activo,
        )

    # ---- Operaciones CRUD ----

    def create(self, proveedor: Proveedor) -> Proveedor:
        """Crea un nuevo proveedor"""
        session = self._get_session()
        try:
            model = ProveedorModel(
                nombre=proveedor.nombre,
                contacto=proveedor.contacto,
                telefono=proveedor.telefono,
                email=proveedor.email,
                notas=proveedor.notas,
                activo=True,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info(f"Proveedor creado: {model.nombre} (ID: {model.id})")
            return self._to_entity(model)
        except Exception as e:
            session.rollback()
            logger.error(f"Error al crear proveedor: {e}")
            raise
        finally:
            session.close()

    def get_all(self, solo_activos: bool = True) -> List[Proveedor]:
        """Lista todos los proveedores activos"""
        session = self._get_session()
        try:
            query = session.query(ProveedorModel)
            if solo_activos:
                query = query.filter(ProveedorModel.activo == True)
            models = query.order_by(ProveedorModel.nombre.asc()).all()
            return [self._to_entity(m) for m in models]
        finally:
            session.close()

    def get_by_id(self, proveedor_id: int) -> Optional[Proveedor]:
        """Obtiene un proveedor por ID"""
        session = self._get_session()
        try:
            model = session.query(ProveedorModel).filter(
                ProveedorModel.id == proveedor_id
            ).first()
            return self._to_entity(model) if model else None
        finally:
            session.close()

    def update(self, proveedor: Proveedor) -> Proveedor:
        """Actualiza un proveedor existente"""
        session = self._get_session()
        try:
            model = session.query(ProveedorModel).filter(
                ProveedorModel.id == proveedor.id
            ).first()
            if not model:
                raise ValueError(f"Proveedor ID {proveedor.id} no encontrado")
            model.nombre = proveedor.nombre
            model.contacto = proveedor.contacto
            model.telefono = proveedor.telefono
            model.email = proveedor.email
            model.notas = proveedor.notas
            session.commit()
            session.refresh(model)
            logger.info(f"Proveedor actualizado: {model.nombre} (ID: {model.id})")
            return self._to_entity(model)
        except Exception as e:
            session.rollback()
            logger.error(f"Error al actualizar proveedor: {e}")
            raise
        finally:
            session.close()

    def delete(self, proveedor_id: int) -> bool:
        """Soft-delete: marca como inactivo"""
        session = self._get_session()
        try:
            model = session.query(ProveedorModel).filter(
                ProveedorModel.id == proveedor_id
            ).first()
            if not model:
                return False
            model.activo = False
            session.commit()
            logger.info(f"Proveedor desactivado: {model.nombre} (ID: {proveedor_id})")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error al desactivar proveedor: {e}")
            raise
        finally:
            session.close()

    # ---- Relación Producto-Proveedor ----

    def asignar_proveedor_a_producto(
        self,
        producto_id: int,
        proveedor_id: int,
        es_principal: bool = True
    ) -> None:
        """
        Asigna (o reemplaza) el proveedor de un producto.
        Si es_principal=True, primero desmarca los otros como no-principales.
        """
        session = self._get_session()
        try:
            # Verificar si ya existe la relación
            existente = session.query(ProductoProveedorModel).filter(
                ProductoProveedorModel.producto_id == producto_id,
                ProductoProveedorModel.proveedor_id == proveedor_id,
            ).first()

            if existente:
                # Solo actualizar bandera principal
                existente.es_principal = es_principal
            else:
                # Si será el principal, quitar ese rol de otros
                if es_principal:
                    session.query(ProductoProveedorModel).filter(
                        ProductoProveedorModel.producto_id == producto_id,
                        ProductoProveedorModel.es_principal == True,
                    ).update({"es_principal": False})

                nuevo = ProductoProveedorModel(
                    producto_id=producto_id,
                    proveedor_id=proveedor_id,
                    es_principal=es_principal,
                )
                session.add(nuevo)

            session.commit()
            logger.info(
                f"Proveedor {proveedor_id} asignado a producto {producto_id} "
                f"(principal={es_principal})"
            )
        except Exception as e:
            session.rollback()
            logger.error(f"Error al asignar proveedor a producto: {e}")
            raise
        finally:
            session.close()

    def remover_proveedor_de_producto(self, producto_id: int) -> None:
        """Elimina todas las relaciones proveedor del producto dado"""
        session = self._get_session()
        try:
            session.query(ProductoProveedorModel).filter(
                ProductoProveedorModel.producto_id == producto_id
            ).delete()
            session.commit()
            logger.info(f"Proveedores removidos del producto {producto_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error al remover proveedores del producto: {e}")
            raise
        finally:
            session.close()

    def get_proveedor_de_producto(self, producto_id: int) -> Optional[Proveedor]:
        """Obtiene el proveedor PRINCIPAL de un producto (retorna None si no hay)"""
        session = self._get_session()
        try:
            rel = session.query(ProductoProveedorModel).filter(
                ProductoProveedorModel.producto_id == producto_id,
                ProductoProveedorModel.es_principal == True,
            ).first()
            if rel and rel.proveedor and rel.proveedor.activo:
                return self._to_entity(rel.proveedor)
            return None
        finally:
            session.close()


__all__ = ["Proveedor", "ProveedorRepository"]
