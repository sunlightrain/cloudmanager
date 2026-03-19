import logging
import ssl
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConnectionConfig:
    host: str
    port: int = 443
    user: str = ""
    password: str = ""
    ssl_context: Optional[ssl.SSLContext] = None
    connection_timeout: int = 30
    pool_size: int = 5
    max_pool_size: int = 10
    idle_timeout: int = 300


@dataclass
class Connection:
    config: ConnectionConfig
    si: Any
    created_at: datetime
    last_used: datetime
    in_use: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)


class ConnectionPoolExhaustedError(Exception):
    pass


class VSphereConnectionPool:
    _instance: Optional['VSphereConnectionPool'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._pools: Dict[str, List[Connection]] = {}
        self._pool_lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = True
        self._initialized = True
        self._start_cleanup_thread()

    def _get_pool_key(self, config: ConnectionConfig) -> str:
        return f"{config.host}:{config.port}:{config.user}"

    def get_connection(self, config: ConnectionConfig) -> Connection:
        pool_key = self._get_pool_key(config)
        
        with self._pool_lock:
            if pool_key not in self._pools:
                self._pools[pool_key] = []
            
            pool = self._pools[pool_key]
            
            for conn in pool:
                if not conn.in_use and self._is_connection_valid(conn):
                    conn.in_use = True
                    conn.last_used = datetime.now()
                    logger.debug(f"Reusing connection for {config.host}")
                    return conn
            
            if len(pool) < config.max_pool_size:
                conn = self._create_connection(config)
                pool.append(conn)
                logger.info(f"Created new connection for {config.host}, pool size: {len(pool)}")
                return conn
            
        raise ConnectionPoolExhaustedError(
            f"Connection pool exhausted for {config.host}, max: {config.max_pool_size}"
        )

    def release_connection(self, conn: Connection):
        with conn.lock:
            conn.in_use = False
            conn.last_used = datetime.now()
        logger.debug(f"Released connection for {conn.config.host}")

    def _create_connection(self, config: ConnectionConfig) -> Connection:
        try:
            from pyVim.connect import SmartConnect, Disconnect
            
            if config.ssl_context:
                si = SmartConnect(
                    host=config.host,
                    port=config.port,
                    user=config.user,
                    pwd=config.password,
                    sslContext=config.ssl_context,
                    connectionTimeout=config.connection_timeout
                )
            else:
                si = SmartConnect(
                    host=config.host,
                    port=config.port,
                    user=config.user,
                    pwd=config.password,
                    connectionTimeout=config.connection_timeout
                )
            
            return Connection(
                config=config,
                si=si,
                created_at=datetime.now(),
                last_used=datetime.now(),
                in_use=True
            )
        except Exception as e:
            logger.error(f"Failed to create connection to {config.host}: {e}")
            raise

    def _is_connection_valid(self, conn: Connection) -> bool:
        if (datetime.now() - conn.last_used).total_seconds() > conn.config.idle_timeout:
            return False
        
        try:
            conn.si.CurrentTime()
            return True
        except Exception:
            return False

    def _cleanup_idle_connections(self):
        while self._running:
            try:
                with self._pool_lock:
                    for pool_key, pool in list(self._pools.items()):
                        for conn in list(pool):
                            if not conn.in_use:
                                if (datetime.now() - conn.last_used).total_seconds() > conn.config.idle_timeout:
                                    try:
                                        from pyVim.connect import Disconnect
                                        Disconnect(conn.si)
                                        pool.remove(conn)
                                        logger.info(f"Cleaned up idle connection for {conn.config.host}")
                                    except Exception as e:
                                        logger.error(f"Error cleaning up connection: {e}")
                        
                        if not pool:
                            del self._pools[pool_key]
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
            
            threading.Event().wait(60)

    def _start_cleanup_thread(self):
        self._cleanup_thread = threading.Thread(target=self._cleanup_idle_connections, daemon=True)
        self._cleanup_thread.start()

    def close_all(self):
        self._running = False
        with self._pool_lock:
            for pool_key, pool in list(self._pools.items()):
                for conn in pool:
                    try:
                        from pyVim.connect import Disconnect
                        Disconnect(conn.si)
                        logger.info(f"Closed connection for {conn.config.host}")
                    except Exception as e:
                        logger.error(f"Error closing connection: {e}")
                pool.clear()
            self._pools.clear()

    def get_pool_status(self) -> Dict[str, Any]:
        with self._pool_lock:
            total = sum(len(pool) for pool in self._pools.values())
            in_use = sum(1 for pool in self._pools.values() for conn in pool if conn.in_use)
            return {
                "total_connections": total,
                "connections_in_use": in_use,
                "available_connections": total - in_use,
                "pool_count": len(self._pools)
            }


_pool: Optional[VSphereConnectionPool] = None


def get_connection_pool() -> VSphereConnectionPool:
    global _pool
    if _pool is None:
        _pool = VSphereConnectionPool()
    return _pool
