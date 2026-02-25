"""
Repositorio para crear y consultar pedidos registrados al proveedor.
"""
from typing import List, Optional, Dict
from datetime import datetime
import logging

from app.infrastructure.models.proveedor import (
    PedidoProveedorModel, DetallePedidoModel
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entidades de dominio ligeras
# ---------------------------------------------------------------------------

class DetallePedido:
    def __init__(
        self,
        producto_id: Optional[int],
        producto_nombre: str,
        cantidad: int,
        precio_unitario: Optional[float] = None,
    ):
        self.producto_id = producto_id
        self.producto_nombre = producto_nombre
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario


class PedidoProveedor:
    def __init__(
        self,
        id: Optional[int] = None,
        proveedor_id: Optional[int] = None,
        proveedor_nombre: Optional[str] = None,
        estado: str = "pendiente",
        notas: Optional[str] = None,
        created_by: Optional[str] = None,
        fecha_pedido: Optional[datetime] = None,
        detalles: Optional[List[DetallePedido]] = None,
    ):
        self.id = id
        self.proveedor_id = proveedor_id
        self.proveedor_nombre = proveedor_nombre
        self.estado = estado
        self.notas = notas
        self.created_by = created_by
        self.fecha_pedido = fecha_pedido
        self.detalles = detalles or []

    @property
    def total_items(self) -> int:
        return sum(d.cantidad for d in self.detalles)


# ---------------------------------------------------------------------------
# Repositorio
# ---------------------------------------------------------------------------

class PedidosRepository:
    """Gestiona la persistencia de pedidos a proveedores"""

    def _get_session(self):
        from app.infrastructure.database import get_session
        return get_session()

    def crear_pedido(
        self,
        proveedor_id: Optional[int],
        proveedor_nombre: Optional[str],
        productos_seleccionados,          # Lista de entidades Producto
        cantidades: Dict[int, int],       # {producto_id: cantidad}
        created_by: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> PedidoProveedor:
        """
        Crea un pedido completo con sus detalles en la base de datos.

        Args:
            proveedor_id: ID del proveedor (puede ser None si no está registrado)
            proveedor_nombre: Nombre del proveedor (snapshot en el momento del pedido)
            productos_seleccionados: Lista de entidades Producto del dominio
            cantidades: dict {producto.id: cantidad_a_pedir}
            created_by: username del usuario autenticado
            notas: Observaciones adicionales

        Returns:
            PedidoProveedor con el ID asignado por la BD
        """
        session = self._get_session()
        try:
            # 1. Crear cabecera del pedido
            pedido_model = PedidoProveedorModel(
                proveedor_id=proveedor_id,
                proveedor_nombre_snapshot=proveedor_nombre,
                estado="pendiente",
                notas=notas,
                created_by=created_by,
            )
            session.add(pedido_model)
            session.flush()  # necesario para obtener el ID antes del commit

            # 2. Crear detalles (una fila por producto)
            for producto in productos_seleccionados:
                cantidad = cantidades.get(producto.id, 1)
                detalle = DetallePedidoModel(
                    pedido_id=pedido_model.id,
                    producto_id=producto.id,
                    producto_nombre_snapshot=producto.nombre,
                    cantidad_solicitada=cantidad,
                    precio_unitario_snapshot=float(producto.precio),
                )
                session.add(detalle)

            session.commit()
            session.refresh(pedido_model)

            logger.info(
                f"Pedido #{pedido_model.id} creado — proveedor: '{proveedor_nombre}' "
                f"— {len(productos_seleccionados)} productos — usuario: {created_by}"
            )

            # 3. Construir entidad de retorno
            detalles_entidad = [
                DetallePedido(
                    producto_id=p.id,
                    producto_nombre=p.nombre,
                    cantidad=cantidades.get(p.id, 1),
                    precio_unitario=float(p.precio),
                )
                for p in productos_seleccionados
            ]

            return PedidoProveedor(
                id=pedido_model.id,
                proveedor_id=proveedor_id,
                proveedor_nombre=proveedor_nombre,
                estado="pendiente",
                notas=notas,
                created_by=created_by,
                fecha_pedido=pedido_model.fecha_pedido,
                detalles=detalles_entidad,
            )

        except Exception as e:
            session.rollback()
            logger.error(f"Error al crear pedido: {e}")
            raise
        finally:
            session.close()

    def get_pedidos_recientes(self, limite: int = 50) -> List[PedidoProveedor]:
        """Lista los pedidos más recientes"""
        session = self._get_session()
        try:
            models = (
                session.query(PedidoProveedorModel)
                .order_by(PedidoProveedorModel.fecha_pedido.desc())
                .limit(limite)
                .all()
            )
            resultado = []
            for m in models:
                detalles = [
                    DetallePedido(
                        producto_id=d.producto_id,
                        producto_nombre=d.producto_nombre_snapshot,
                        cantidad=d.cantidad_solicitada,
                        precio_unitario=float(d.precio_unitario_snapshot) if d.precio_unitario_snapshot else None,
                    )
                    for d in m.detalles
                ]
                resultado.append(PedidoProveedor(
                    id=m.id,
                    proveedor_id=m.proveedor_id,
                    proveedor_nombre=m.proveedor_nombre_snapshot,
                    estado=m.estado,
                    notas=m.notas,
                    created_by=m.created_by,
                    fecha_pedido=m.fecha_pedido,
                    detalles=detalles,
                ))
            return resultado
        finally:
            session.close()

    def update_proveedor_pedido(self, pedido_id: int, proveedor_id: int, proveedor_nombre: str) -> bool:
        """Actualiza el proveedor de un pedido existente."""
        session = self._get_session()
        try:
            model = session.query(PedidoProveedorModel).filter_by(id=pedido_id).first()
            if not model:
                return False
            model.proveedor_id = proveedor_id
            model.proveedor_nombre_snapshot = proveedor_nombre
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_estado_pedido(self, pedido_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un pedido existente (ej: 'enviado', 'recibido')."""
        session = self._get_session()
        try:
            model = session.query(PedidoProveedorModel).filter_by(id=pedido_id).first()
            if not model:
                return False
            model.estado = nuevo_estado
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


__all__ = ["PedidosRepository", "PedidoProveedor", "DetallePedido"]
