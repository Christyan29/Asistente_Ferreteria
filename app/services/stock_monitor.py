"""
Servicio de monitoreo automático de stock bajo.
Usa QTimer para verificar periódicamente sin bloquear la UI.
Solo dispara señales cuando encuentra productos bajo el mínimo.
"""
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
import logging

logger = logging.getLogger(__name__)

# 20 minutos en milisegundos
INTERVALO_MS = 20 * 60 * 1000


class StockMonitorService(QObject):
    """
    Monitor de stock que corre en el hilo de la UI usando QTimer.
    NO usa hilos secundarios (evita problemas con SQLite y Qt).

    Señales emitidas:
        alertas_detectadas(list): lista de entidades Producto con stock bajo
    """

    alertas_detectadas = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._timer = QTimer(self)
        self._timer.setInterval(INTERVALO_MS)
        self._timer.timeout.connect(self._verificar)

        # IDs de productos ya notificados en esta sesión (evita re-notificar)
        self._productos_notificados: set = set()

        # Flag para saber si el monitor está activo
        self._activo = False

        logger.info(f"StockMonitorService creado (intervalo: {INTERVALO_MS // 60000} min)")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def iniciar(self, verificar_ahora: bool = True) -> None:
        """
        Inicia el timer de monitoreo.

        Args:
            verificar_ahora: Si True, hace una verificación INMEDIATA
                             antes de esperar el primer intervalo.
                             Usar True al autenticarse por primera vez.
        """
        if self._activo:
            return

        self._activo = True
        self._timer.start()
        logger.info("StockMonitorService iniciado")

        if verificar_ahora:
            # Pequeño delay para que la UI ya esté visible
            QTimer.singleShot(800, self._verificar)

    def detener(self) -> None:
        """Detiene el timer y resetea la sesión de notificaciones."""
        if not self._activo:
            return

        self._timer.stop()
        self._activo = False
        self._productos_notificados.clear()
        logger.info("StockMonitorService detenido y estado de sesión limpiado")

    def resetear_notificaciones(self) -> None:
        """
        Limpia los IDs ya notificados.
        Útil para forzar una nueva evaluación sin reiniciar el timer.
        """
        self._productos_notificados.clear()
        logger.debug("Notificaciones de monitor reseteadas")

    @property
    def activo(self) -> bool:
        return self._activo

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _verificar(self) -> None:
        """
        Consulta la BD buscando productos con stock bajo.
        Solo emite la señal si hay productos NUEVOS (no notificados aún).
        """
        try:
            from app.infrastructure.product_repository import ProductRepository
            repo = ProductRepository()
            todos_bajo_stock = repo.get_low_stock()

            if not todos_bajo_stock:
                logger.debug("Monitor: sin productos con stock bajo")
                return

            # Filtrar los que ya se notificaron en esta sesión
            nuevos = [
                p for p in todos_bajo_stock
                if p.id not in self._productos_notificados
            ]

            if not nuevos:
                logger.debug(
                    f"Monitor: {len(todos_bajo_stock)} con stock bajo "
                    f"pero ya notificados en esta sesión"
                )
                return

            # Registrar como notificados
            for p in nuevos:
                self._productos_notificados.add(p.id)

            logger.info(
                f"Monitor: {len(nuevos)} producto(s) con stock bajo detectados — "
                f"emitiendo señal alertas_detectadas"
            )
            self.alertas_detectadas.emit(nuevos)

        except Exception as e:
            logger.error(f"Error en verificación de stock del monitor: {e}")


__all__ = ["StockMonitorService", "INTERVALO_MS"]
