"""
Tools Module for Family AI Assistant
====================================

Este módulo contiene las herramientas personalizadas (@tool decorators)
que el LLM puede usar para interactuar con los datos del usuario.

Estructura:
    - finance.py: Herramientas para gestión de finanzas
    - health.py: Herramientas para tracking de hábitos y salud
    - docs.py: Herramientas para búsqueda en documentos (RAG) [próxima]

Patrón: Replicado de 2_Chatbot_Agent.py
- Cada herramienta tiene @tool decorator
- Docstrings detallados para que el LLM entienda cuándo usarlas
- Type hints completos
- Manejo de errores robusto
- Logging para debugging

Uso en src/graph.py:
    from src.tools import all_tools
    llm_with_tools = llm.bind_tools(all_tools)
"""

# =============================================================================
# IMPORT ALL TOOLS
# =============================================================================

from src.tools.finance import (
    add_expense,
    check_budget,
    get_balance,
    get_spending_insights,
    finance_tools,
)

from src.tools.health import (
    log_habit,
    check_habit_progress,
    get_health_summary,
    get_habit_motivation,
    health_tools,
)

from src.tools.docs import (
    retrieve_documents,
    search_by_category,
    list_all_documents,
    doc_tools,
)

from src.tools.drive_mcp import (
    load_mcp_tools,
    get_mcp_tools,
    create_drive_tools_mock,
    initialize_mcp_connection,
)

# =============================================================================
# EXPORT ALL TOOLS
# =============================================================================

# Lista completa de todas las herramientas disponibles
all_tools = finance_tools + health_tools + doc_tools
"""
Lista de TODAS las herramientas disponibles para el LLM.
Se usará en src/graph.py para bind al modelo.

Herramientas de Finanzas (4):
    - add_expense: Registrar gasto
    - check_budget: Ver presupuesto disponible
    - get_balance: Ver resumen financiero
    - get_spending_insights: Consejos de gasto

Herramientas de Salud (4):
    - log_habit: Registrar hábito completado
    - check_habit_progress: Ver progreso de hábito
    - get_health_summary: Ver dashboard de salud
    - get_habit_motivation: Obtener motivación

Herramientas de Documentos (3):
    - retrieve_documents: Buscar en documentos por palabra clave
    - search_by_category: Filtrar documentos por categoría
    - list_all_documents: Listar todos los documentos disponibles

Herramientas de Google Drive (MCP - Dinámicas):
    - list_drive_files: Listar archivos en Google Drive
    - read_drive_file: Leer contenido de archivos
    (Se cargan dinámicamente desde servidor MCP)
"""

# Dictionaries para acceso por categoría
TOOLS_BY_CATEGORY = {
    "finance": finance_tools,
    "health": health_tools,
    "docs": doc_tools,
    "drive": [],  # Se llena dinámicamente con herramientas MCP
}
"""Acceso a herramientas por categoría para routing más específico."""

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Finance tools
    "add_expense",
    "check_budget",
    "get_balance",
    "get_spending_insights",
    "finance_tools",
    # Health tools
    "log_habit",
    "check_habit_progress",
    "get_health_summary",
    "get_habit_motivation",
    "health_tools",
    # Document tools
    "retrieve_documents",
    "search_by_category",
    "list_all_documents",
    "doc_tools",
    # Drive MCP tools
    "load_mcp_tools",
    "get_mcp_tools",
    "create_drive_tools_mock",
    "initialize_mcp_connection",
    # All tools
    "all_tools",
    "TOOLS_BY_CATEGORY",
]
