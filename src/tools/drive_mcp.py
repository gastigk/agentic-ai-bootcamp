"""
Google Drive MCP Integration
============================

Módulo para conectar al agente con servidores MCP que permiten acceso a Google Drive.

Patrón Replicado: 4_MCP_Agent.py (líneas 1-254)
- MultiServerMCPClient para conexión a servidores MCP
- Manejo asincrónico con asyncio
- Obtención dinámicas de herramientas
- Integración con LangChain

El servidor MCP esperado debe exponer herramientas para:
- list_files(path: str): Lista archivos en una ruta
- read_file(file_id: str): Lee contenido de un archivo

Servidor MCP típico:
  - URL: http://localhost:3000 (o configurada)
  - Transporte: streamable_http
  - Herramientas: list_files, read_file

Ejemplo de uso:
  >>> import asyncio
  >>> from src.tools.drive_mcp import load_mcp_tools
  >>>
  >>> async def main():
  >>>     tools = await load_mcp_tools("http://localhost:3000")
  >>>     for tool in tools:
  >>>         print(f"- {tool.name}")
  >>>
  >>> asyncio.run(main())
"""

# =============================================================================
# IMPORTS
# =============================================================================

import asyncio
import logging
from typing import List, Optional, Dict, Any
from functools import wraps

# Importar cliente MCP
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[DRIVE MCP] ⚠️ langchain_mcp_adapters no disponible")
    print("[DRIVE MCP] Instala: pip install langchain_mcp_adapters")

from langchain_core.tools import Tool


# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)

def setup_logger():
    """Configura logging para debug."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[DRIVE MCP LOG] %(levelname)s: %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

setup_logger()


# =============================================================================
# MCP CLIENT MANAGEMENT
# =============================================================================

class MCPClientManager:
    """
    Gestor singleton para conexiones MCP.
    
    Evita múltiples instancias del cliente conectando a mismo servidor.
    """
    
    _instance: Optional['MCPClientManager'] = None
    _client: Optional[MultiServerMCPClient] = None
    _server_url: Optional[str] = None
    _loop: Optional[asyncio.AbstractEventLoop] = None
    
    def __new__(cls):
        """Patrón singleton."""
        if cls._instance is None:
            cls._instance = super(MCPClientManager, cls).__new__(cls)
        return cls._instance
    
    async def connect(self, server_url: str = "http://localhost:3000") -> MultiServerMCPClient:
        """
        Conecta al servidor MCP.
        
        Args:
            server_url: URL del servidor MCP
            
        Returns:
            MultiServerMCPClient conectado
            
        Raises:
            ValueError: Si MCP no está disponible
            Exception: Si la conexión falla
        """
        if not MCP_AVAILABLE:
            raise ValueError(
                "❌ MCP no disponible. Instala: pip install langchain_mcp_adapters"
            )
        
        # Reutilizar conexión existente
        if self._client is not None and self._server_url == server_url:
            logger.info(f"Reutilizando conexión existente a {server_url}")
            return self._client
        
        try:
            logger.info(f"Conectando a servidor MCP: {server_url}")
            
            # Configurar cliente MCP
            mcp_config = {
                "server": {
                    "url": server_url,
                    "transport": "streamable_http",  # Usar HTTP streaming
                }
            }
            
            # Crear cliente
            self._client = MultiServerMCPClient(mcp_config)
            self._server_url = server_url
            
            logger.info(f"✅ Conectado a {server_url}")
            
            return self._client
            
        except Exception as e:
            logger.error(f"❌ Error conectando a MCP: {e}")
            raise
    
    async def disconnect(self):
        """Desconecta del servidor MCP."""
        if self._client is not None:
            try:
                # Cerrar conexión si es posible
                if hasattr(self._client, 'close'):
                    await self._client.close()
                logger.info("Desconectado del servidor MCP")
            except Exception as e:
                logger.warning(f"Error al desconectar: {e}")
            finally:
                self._client = None
                self._server_url = None


# =============================================================================
# LOAD MCP TOOLS
# =============================================================================

async def load_mcp_tools(
    server_url: str = "http://localhost:3000"
) -> List[Tool]:
    """
    Carga las herramientas disponibles en el servidor MCP.
    
    Este es el punto de entrada principal para integrar MCP en el agente.
    
    Patrón Replicado: 4_MCP_Agent.py (líneas 131-138)
    - Conecta al cliente MCP
    - Obtiene herramientas disponibles
    - Las retorna compatibles con LangChain
    
    Herramientas esperadas del servidor MCP:
    - list_files(path: str): Lista archivos en ruta de Google Drive
    - read_file(file_id: str): Lee contenido de archivo
    
    Args:
        server_url: URL del servidor MCP
                   Default: "http://localhost:3000"
    
    Returns:
        List[Tool]: Lista de herramientas LangChain
        
    Raises:
        ValueError: Si MCP no está disponible
        Exception: Si la conexión o carga de herramientas falla
    
    Example:
        >>> import asyncio
        >>> tools = await load_mcp_tools()
        >>> print(f"Herramientas cargadas: {len(tools)}")
        >>> for tool in tools:
        >>>     print(f"  - {tool.name}: {tool.description}")
    """
    
    if not MCP_AVAILABLE:
        logger.error("❌ MCP no disponible")
        raise ValueError(
            "MCP no disponible. Instala: pip install langchain_mcp_adapters"
        )
    
    try:
        logger.info(f"📥 Cargando herramientas MCP desde {server_url}")
        
        # Obtener cliente
        manager = MCPClientManager()
        client = await manager.connect(server_url)
        
        # Obtener herramientas del servidor
        logger.info("⏳ Consultando herramientas disponibles...")
        tools = await client.get_tools()
        
        logger.info(f"✅ {len(tools)} herramientas cargadas")
        for tool in tools:
            logger.info(f"   - {tool.name}: {tool.description[:50]}...")
        
        return tools
        
    except Exception as e:
        logger.error(f"❌ Error cargando herramientas: {e}")
        raise


# =============================================================================
# ASYNC WRAPPER FOR STREAMLIT
# =============================================================================

def run_async(func):
    """
    Decorador para ejecutar funciones async en Streamlit.
    
    Streamlit no soporta async nativamente, así que este decorador
    crea un event loop cuando es necesario.
    
    Patrón Replicado: 4_MCP_Agent.py (líneas 168-185)
    - Crea un nuevo event loop
    - Ejecuta la función async
    - Limpia el loop después
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Obtener loop existente o crear uno nuevo
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(func(*args, **kwargs))
        finally:
            # No cerrar el loop, por si lo necesita Streamlit
            pass
    
    return wrapper


# =============================================================================
# WRAPPER FUNCTIONS (SYNC) FOR LANGGRAPH
# =============================================================================

@run_async
async def get_mcp_tools(server_url: str = "http://localhost:3000") -> List[Tool]:
    """
    Wrapper síncrono para obtener herramientas MCP.
    
    Uso en LangGraph (que requiere funciones síncronas):
    
        from src.tools.drive_mcp import get_mcp_tools
        
        mcp_tools = get_mcp_tools("http://localhost:3000")
        # mcp_tools contiene las herramientas del servidor
    
    Args:
        server_url: URL del servidor MCP
    
    Returns:
        List[Tool]: Herramientas de MCP
    """
    return await load_mcp_tools(server_url)


# =============================================================================
# DRIVE-SPECIFIC TOOLS (SIMULADAS)
# =============================================================================

def create_drive_tools_mock() -> List[Tool]:
    """
    Crea herramientas simuladas de Google Drive para desarrollo sin MCP real.
    
    Útil para testing cuando no hay un servidor MCP disponible.
    
    Returns:
        List[Tool]: Herramientas simuladas
    """
    
    # Mock data: archivos simulados en Google Drive
    MOCK_DRIVE_FILES = {
        "root": [
            {"id": "file_1", "name": "Presupuesto Familiar 2025.xlsx", "type": "file"},
            {"id": "file_2", "name": "Documentos Importantes", "type": "folder"},
            {"id": "file_3", "name": "Fotos Vacaciones", "type": "folder"},
        ],
        "Documentos Importantes": [
            {"id": "file_4", "name": "Póliza de Seguro.pdf", "type": "file"},
            {"id": "file_5", "name": "Contrato Arrendamiento.pdf", "type": "file"},
        ]
    }
    
    MOCK_FILE_CONTENTS = {
        "file_4": "Póliza de Seguro de Auto\nAsegurador: Global Insurance\nVigencia: 2025-01-01 a 2026-01-01\n...",
        "file_5": "Contrato de Arrendamiento\nArrendador: Property Corp\nRenta mensual: $1,200\n...",
    }
    
    def list_drive_files(path: str = "root") -> str:
        """
        Lista archivos en una ruta de Google Drive.
        
        Args:
            path: Ruta en Google Drive ("root" para raíz)
        
        Returns:
            String con lista de archivos
        """
        files = MOCK_DRIVE_FILES.get(path, [])
        
        if not files:
            return f"No hay archivos en {path}"
        
        result = f"Archivos en {path}:\n"
        for file in files:
            file_type = "📁" if file["type"] == "folder" else "📄"
            result += f"  {file_type} {file['name']} (id: {file['id']})\n"
        
        return result
    
    def read_drive_file(file_id: str) -> str:
        """
        Lee el contenido de un archivo de Google Drive.
        
        Args:
            file_id: ID del archivo
        
        Returns:
            Contenido del archivo
        """
        content = MOCK_FILE_CONTENTS.get(file_id)
        
        if content is None:
            return f"Archivo {file_id} no encontrado o no es legible"
        
        return content
    
    # Crear herramientas LangChain
    tools = [
        Tool(
            name="list_drive_files",
            func=list_drive_files,
            description=(
                "Lista archivos en Google Drive. "
                "Use 'root' para la raíz, o el nombre de una carpeta."
            )
        ),
        Tool(
            name="read_drive_file",
            func=read_drive_file,
            description=(
                "Lee el contenido de un archivo de Google Drive. "
                "Requiere el ID del archivo (obtenido de list_drive_files)."
            )
        ),
    ]
    
    logger.info("✅ Herramientas de Google Drive (mock) creadas")
    
    return tools


# =============================================================================
# PUBLIC API
# =============================================================================

async def initialize_mcp_connection(
    server_url: str = "http://localhost:3000",
    fallback_to_mock: bool = True
) -> List[Tool]:
    """
    Inicializa la conexión MCP y obtiene herramientas.
    
    Punto de entrada principal para integración con el agente.
    
    Patrón: Intenta conectar a MCP real, fallback a mock si falla.
    
    Args:
        server_url: URL del servidor MCP
        fallback_to_mock: Si True, usa mock si MCP no está disponible
    
    Returns:
        List[Tool]: Herramientas disponibles
    """
    
    try:
        # Intentar conectar a MCP real
        logger.info(f"[INITIALIZE] Intentando conectar a MCP en {server_url}")
        tools = await load_mcp_tools(server_url)
        logger.info(f"[INITIALIZE] ✅ Conectado a MCP real")
        return tools
        
    except Exception as e:
        logger.warning(f"[INITIALIZE] ⚠️ No se pudo conectar a MCP: {e}")
        
        if fallback_to_mock:
            logger.info("[INITIALIZE] 🔄 Usando herramientas mock")
            return create_drive_tools_mock()
        else:
            raise


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "load_mcp_tools",
    "get_mcp_tools",
    "create_drive_tools_mock",
    "initialize_mcp_connection",
    "MCPClientManager",
    "run_async",
]
