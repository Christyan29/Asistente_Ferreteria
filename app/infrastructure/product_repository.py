"""
Repositorio para operaciones CRUD de productos.
Implementa el patrón Repository para abstraer el acceso a datos.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from decimal import Decimal
import logging

from app.domain.producto import Producto
from app.domain.categoria import Categoria
from app.infrastructure.models.producto import ProductoModel, CategoriaModel
from app.infrastructure.database import session_scope

logger = logging.getLogger(__name__)


class ProductRepository:
    """Repositorio para gestionar productos en la base de datos"""

    def __init__(self, session: Optional[Session] = None):
        """
        Inicializa el repositorio.

        Args:
            session: Sesión de SQLAlchemy (opcional, se crea una si no se proporciona)
        """
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        """Obtiene la sesión actual o crea una nueva"""
        if self.session:
            return self.session
        from app.infrastructure.database import get_session
        return get_session()

    def _model_to_entity(self, model: ProductoModel) -> Producto:
        """Convierte un modelo ORM a entidad de dominio"""
        return Producto(
            id=model.id,
            codigo=model.codigo,
            nombre=model.nombre,
            descripcion=model.descripcion,
            precio=Decimal(str(model.precio)),
            stock=model.stock,
            stock_minimo=model.stock_minimo,
            unidad_medida=model.unidad_medida,
            categoria_id=model.categoria_id,
            categoria_nombre=model.categoria.nombre if model.categoria else None,
            marca=model.marca,
            ubicacion=model.ubicacion,
            activo=model.activo,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_model(self, entity: Producto, model: Optional[ProductoModel] = None) -> ProductoModel:
        """Convierte una entidad de dominio a modelo ORM"""
        if model is None:
            model = ProductoModel()

        model.codigo = entity.codigo
        model.nombre = entity.nombre
        model.descripcion = entity.descripcion
        model.precio = float(entity.precio)
        model.stock = entity.stock
        model.stock_minimo = entity.stock_minimo
        model.unidad_medida = entity.unidad_medida
        model.categoria_id = entity.categoria_id
        model.marca = entity.marca
        model.ubicacion = entity.ubicacion
        model.activo = entity.activo

        return model

    def create(self, producto: Producto) -> Producto:
        """
        Crea un nuevo producto en la base de datos.

        Args:
            producto: Entidad de producto a crear

        Returns:
            Producto creado con ID asignado
        """
        session = self._get_session()
        try:
            model = self._entity_to_model(producto)
            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info(f"Producto creado: {model.nombre} (ID: {model.id})")
            return self._model_to_entity(model)
        except Exception as e:
            session.rollback()
            logger.error(f"Error al crear producto: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def get_by_id(self, producto_id: int) -> Optional[Producto]:
        """
        Obtiene un producto por su ID.

        Args:
            producto_id: ID del producto

        Returns:
            Producto si existe, None en caso contrario
        """
        session = self._get_session()
        try:
            model = session.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
            return self._model_to_entity(model) if model else None
        finally:
            if self._owns_session:
                session.close()

    def get_by_codigo(self, codigo: str) -> Optional[Producto]:
        """
        Obtiene un producto por su código.

        Args:
            codigo: Código del producto

        Returns:
            Producto si existe, None en caso contrario
        """
        session = self._get_session()
        try:
            model = session.query(ProductoModel).filter(ProductoModel.codigo == codigo.upper()).first()
            return self._model_to_entity(model) if model else None
        finally:
            if self._owns_session:
                session.close()

    def get_all(self, solo_activos: bool = True) -> List[Producto]:
        """
        Obtiene todos los productos.

        Args:
            solo_activos: Si True, solo retorna productos activos

        Returns:
            Lista de productos
        """
        session = self._get_session()
        try:
            query = session.query(ProductoModel)
            if solo_activos:
                query = query.filter(ProductoModel.activo == True)
            models = query.all()
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._owns_session:
                session.close()

    def search(self, query: str, solo_activos: bool = True) -> List[Producto]:
        """
        Busca productos por nombre, código o descripción.

        Args:
            query: Texto a buscar
            solo_activos: Si True, solo busca en productos activos

        Returns:
            Lista de productos que coinciden con la búsqueda
        """
        session = self._get_session()
        try:
            search_pattern = f"%{query}%"
            db_query = session.query(ProductoModel).filter(
                or_(
                    ProductoModel.nombre.ilike(search_pattern),
                    ProductoModel.codigo.ilike(search_pattern),
                    ProductoModel.descripcion.ilike(search_pattern),
                    ProductoModel.marca.ilike(search_pattern),
                )
            )

            if solo_activos:
                db_query = db_query.filter(ProductoModel.activo == True)

            models = db_query.all()
            logger.info(f"Búsqueda '{query}': {len(models)} resultados")
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._owns_session:
                session.close()

    def get_by_categoria(self, categoria_id: int, solo_activos: bool = True) -> List[Producto]:
        """
        Obtiene productos de una categoría específica.

        Args:
            categoria_id: ID de la categoría
            solo_activos: Si True, solo retorna productos activos

        Returns:
            Lista de productos de la categoría
        """
        session = self._get_session()
        try:
            query = session.query(ProductoModel).filter(ProductoModel.categoria_id == categoria_id)
            if solo_activos:
                query = query.filter(ProductoModel.activo == True)
            models = query.all()
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._owns_session:
                session.close()

    def get_stock_bajo(self) -> List[Producto]:
        """
        Obtiene productos con stock bajo (stock <= stock_minimo).

        Returns:
            Lista de productos con stock bajo
        """
        session = self._get_session()
        try:
            models = session.query(ProductoModel).filter(
                and_(
                    ProductoModel.stock <= ProductoModel.stock_minimo,
                    ProductoModel.activo == True
                )
            ).all()
            logger.info(f"Productos con stock bajo: {len(models)}")
            return [self._model_to_entity(m) for m in models]
        finally:
            if self._owns_session:
                session.close()

    def update(self, producto: Producto) -> Producto:
        """
        Actualiza un producto existente.

        Args:
            producto: Producto con datos actualizados

        Returns:
            Producto actualizado
        """
        session = self._get_session()
        try:
            model = session.query(ProductoModel).filter(ProductoModel.id == producto.id).first()
            if not model:
                raise ValueError(f"Producto con ID {producto.id} no encontrado")

            self._entity_to_model(producto, model)
            session.commit()
            session.refresh(model)
            logger.info(f"Producto actualizado: {model.nombre} (ID: {model.id})")
            return self._model_to_entity(model)
        except Exception as e:
            session.rollback()
            logger.error(f"Error al actualizar producto: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def delete(self, producto_id: int, soft_delete: bool = True) -> bool:
        """
        Elimina un producto.

        Args:
            producto_id: ID del producto a eliminar
            soft_delete: Si True, solo marca como inactivo; si False, elimina físicamente

        Returns:
            True si se eliminó correctamente
        """
        session = self._get_session()
        try:
            model = session.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
            if not model:
                return False

            if soft_delete:
                model.activo = False
                session.commit()
                logger.info(f"Producto desactivado: {model.nombre} (ID: {model.id})")
            else:
                session.delete(model)
                session.commit()
                logger.info(f"Producto eliminado: {model.nombre} (ID: {producto_id})")

            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error al eliminar producto: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def actualizar_stock(self, producto_id: int, cantidad: int) -> Producto:
        """
        Actualiza el stock de un producto.

        Args:
            producto_id: ID del producto
            cantidad: Cantidad a agregar (positivo) o quitar (negativo)

        Returns:
            Producto actualizado
        """
        session = self._get_session()
        try:
            model = session.query(ProductoModel).filter(ProductoModel.id == producto_id).first()
            if not model:
                raise ValueError(f"Producto con ID {producto_id} no encontrado")

            nuevo_stock = model.stock + cantidad
            if nuevo_stock < 0:
                raise ValueError(f"Stock insuficiente. Stock actual: {model.stock}, cantidad solicitada: {abs(cantidad)}")

            model.stock = nuevo_stock
            session.commit()
            session.refresh(model)
            logger.info(f"Stock actualizado: {model.nombre} - Nuevo stock: {model.stock}")
            return self._model_to_entity(model)
        except Exception as e:
            session.rollback()
            logger.error(f"Error al actualizar stock: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()


class CategoriaRepository:
    """Repositorio para gestionar categorías"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self._owns_session = session is None

    def _get_session(self) -> Session:
        if self.session:
            return self.session
        from app.infrastructure.database import get_session
        return get_session()

    def create(self, categoria: Categoria) -> Categoria:
        """Crea una nueva categoría"""
        session = self._get_session()
        try:
            model = CategoriaModel(
                nombre=categoria.nombre,
                descripcion=categoria.descripcion,
                activo=categoria.activo
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info(f"Categoría creada: {model.nombre}")

            categoria.id = model.id
            categoria.created_at = model.created_at
            categoria.updated_at = model.updated_at
            return categoria
        except Exception as e:
            session.rollback()
            logger.error(f"Error al crear categoría: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()

    def get_all(self, solo_activas: bool = True) -> List[Categoria]:
        """Obtiene todas las categorías"""
        session = self._get_session()
        try:
            query = session.query(CategoriaModel)
            if solo_activas:
                query = query.filter(CategoriaModel.activo == True)
            models = query.all()

            return [
                Categoria(
                    id=m.id,
                    nombre=m.nombre,
                    descripcion=m.descripcion,
                    activo=m.activo,
                    created_at=m.created_at,
                    updated_at=m.updated_at
                )
                for m in models
            ]
        finally:
            if self._owns_session:
                session.close()


__all__ = ["ProductRepository", "CategoriaRepository"]
