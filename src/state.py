"""
State Management for Family AI Assistant
==========================================

Defines the core AgentState using LangGraph's StateGraph pattern.
Replicates the TypedDict + Annotated pattern from 1_Basic_Chatbot.py,
but enriched with domain-specific fields for the Family Assistant use case.

Key Fields:
    - messages: Conversation history (core pattern from bootcamp)
    - user_id: Database reference to identify the user
    - active_goals: Dynamic objectives loaded from PostgreSQL
    - current_context: Router's routing decision ("finance", "health", "docs", "general")
"""

# =============================================================================
# IMPORTS
# =============================================================================

from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict

# LangGraph message utilities
from langgraph.graph.message import add_messages

# Pydantic for data validation (required per copilot-rules.md)
from pydantic import BaseModel, Field


# =============================================================================
# PYDANTIC MODELS FOR VALIDATED DATA
# =============================================================================

class Goal(BaseModel):
    """
    Representa un objetivo del usuario cargado desde PostgreSQL.
    Ejemplo: {"name": "ahorro", "target": 500, "current": 150, "unit": "USD"}
    """
    name: str = Field(..., description="Nombre del objetivo (ej: 'ahorro', 'gym')")
    target: float = Field(..., description="Valor objetivo a alcanzar")
    current: float = Field(..., description="Progreso actual")
    unit: str = Field(default="", description="Unidad de medida (USD, días, veces, etc)")
    deadline: Optional[str] = Field(None, description="Fecha límite en formato ISO")


class UserContext(BaseModel):
    """
    Contexto del usuario persistido en la sesión.
    Se carga una vez de PostgreSQL al iniciar.
    """
    user_id: str = Field(..., description="Identificador único del usuario")
    name: str = Field(..., description="Nombre del usuario")
    goals: List[Goal] = Field(default_factory=list, description="Objetivos activos del mes")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferencias del usuario")


# =============================================================================
# LANGGRAPH STATE (Referencia: 1_Basic_Chatbot.py)
# =============================================================================

class AgentState(TypedDict):
    """
    Estado central del grafo LangGraph.
    Siguiendo el patrón de TypedDict + Annotated del bootcamp.

    Este estado se pasa entre nodos del grafo y contiene:
    - El historial conversacional completo
    - Contexto del usuario (cargado de PostgreSQL)
    - Decisión de enrutamiento del Router
    - Información enriquecida para tomar decisiones informadas

    Uso:
        graph = StateGraph(AgentState)
        graph.add_node("router", router_node)
        ...
    """

    # ========== Core Conversation (from 1_Basic_Chatbot.py) ==========
    messages: Annotated[
        List[dict],
        add_messages,  # ✅ Permite agregar mensajes eficientemente
    ]
    """
    Historial de mensajes. Cada mensaje es un dict con estructura:
    {"role": "user" | "assistant", "content": "...", "timestamp": "..."}
    """

    # ========== User Context (loaded from PostgreSQL) ==========
    user_id: str
    """
    Identificador único del usuario.
    Se usa para cargar los Objetivos de la DB.
    """

    active_goals: Dict[str, Goal]
    """
    Objetivos del mes cargados de PostgreSQL.
    Estructura: {"ahorro": Goal(...), "gym": Goal(...)}
    Ejemplo uso en prompt:
        "El usuario quiere ahorrar $500. Ya ha gastado $150 este mes."
    """

    current_context: str
    """
    Decisión del Router sobre qué especialista activar.
    Valores permitidos: "finance", "health", "docs", "general", "unknown"
    
    Determinado por:
    1. El Router analiza el mensaje del usuario
    2. Los objetivos activos de ese usuario
    3. Decide cuál es el contexto relevante
    
    Ejemplo: Si el user_id=123 tiene goal["ahorro"] y pregunta "¿Cuánto he gastado?",
    el router pone current_context="finance"
    """

    # ========== Optional RAG Context (for document Q&A) ==========
    retrieved_docs: Optional[List[dict]] = None
    """
    Documentos recuperados si el contexto es "docs" (RAG agentico).
    Estructura: [{"content": "...", "score": 0.95, "source": "..."}]
    """

    # ========== Agent Reasoning (for transparency in UI) ==========
    reasoning_steps: Optional[List[str]] = None
    """
    Pasos internos del agente para mostrar en st.expander (ver copilot-rules.md).
    Facilita el debugging y transparencia en el proceso del agente.
    
    Ejemplo: ["Detect finance context", "Load user spending", "Generate response"]
    """

    # ========== Metadata ==========
    session_id: Optional[str] = None
    """
    ID de sesión para tracking. Generado al iniciar la app Streamlit.
    """


# =============================================================================
# TYPE ALIASES FOR CLARITY
# =============================================================================

RouterDecision = str
"""
Tipo para las decisiones del router: "finance" | "health" | "docs" | "general"
"""

ToolOutput = Dict[str, Any]
"""
Tipo para salida de herramientas (tools). Típicamente JSON con resultado o error.
"""


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def create_initial_state(user_id: str, goals: Optional[List[Goal]] = None) -> AgentState:
    """
    Factory function para crear un AgentState inicial.
    Útil al iniciar una conversación o sesión.

    Args:
        user_id: ID del usuario
        goals: Lista de objetivos (si None, se usa lista vacía)

    Returns:
        AgentState inicializado

    Ejemplo:
        state = create_initial_state("user_123", goals=[Goal(...)])
    """
    goals_dict = {goal.name: goal for goal in (goals or [])}

    return AgentState(
        messages=[],
        user_id=user_id,
        active_goals=goals_dict,
        current_context="unknown",
        retrieved_docs=None,
        reasoning_steps=[],
        session_id=None,
    )
