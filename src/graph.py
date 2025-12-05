"""
Main Agent Graph - StateGraph Orchestration
=============================================

Módulo central que orquesta el flujo conversacional del AI Assistant.
Implementa el patrón LangGraph con StateGraph + condicional edges.

Patrón Replicado: 1_Basic_Chatbot.py (líneas 39-51)
- StateGraph(AgentState) para gestión de estado
- Nodos especializados para cada dominio
- Tool binding con llm.bind_tools()
- Conditional edges para routing dinámico

Arquitectura:
    START
      ↓
    router_node → Clasifica contexto (finance/health/docs/general)
      ↓
    ┌─────────────────────────────────────┐
    ↓         ↓         ↓              ↓
  finance  health    docs          general
  _node    _node    _node          _node
    ↓         ↓         ↓              ↓
    └─────────────────────────────────────┘
      ↓
    END

Cada nodo especializado:
- Vincula herramientas específicas del dominio
- Inyecta System Prompt personalizado
- Invoca LLM con contexto del usuario
- Retorna mensaje de IA con herramientas ejecutadas

Flujo de datos: AgentState (messages, user_id, active_goals, current_context)
"""

# =============================================================================
# IMPORTS
# =============================================================================

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessage,
    BaseMessage,
)
from langchain_openai import ChatOpenAI

from src.state import AgentState
from src.tools import (
    finance_tools,
    health_tools,
    doc_tools,
)
from src.rag import compile_rag_graph, create_initial_rag_state
from src.tools.docs import retrieve_documents

import os
from typing import Any, Literal


# =============================================================================
# LLM INITIALIZATION (Global - se pasa en build_workflow)
# =============================================================================

def _get_llm():
    """
    Inicializa el modelo de LLM.
    
    Usa OPENAI_API_KEY de environment o env variable.
    Modelo: gpt-4o-mini (rápido y económico para agente)
    
    Returns:
        ChatOpenAI instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ OPENAI_API_KEY no configurada")
    
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=api_key,
    )


# =============================================================================
# NODE: ROUTER
# =============================================================================

def router_node(state: AgentState) -> dict:
    """
    Nodo de enrutamiento: Clasifica el contexto de la conversación.
    
    Este es el primer nodo que se ejecuta. Analiza el último mensaje
    del usuario para determinar a cuál especialista (nodo) debe dirigirse.
    
    Clasificación (simple keyword matching):
    - "finance": Palabras como dinero, gasto, presupuesto, gastos, financiero, salario
    - "health": Palabras como ejercicio, hábito, salud, gym, deporte, médico, medicina
    - "docs": Palabras como documento, contrato, póliza, información, buscar, seguro
    - "general": Cualquier otra cosa (charla casual)
    
    Args:
        state: AgentState con messages, user_id, active_goals, etc.
        
    Returns:
        dict con {"current_context": str} actualizado
        
    Future Enhancement:
        - Usar LLM lightweight para clasificación más precisa
        - Análisis de active_goals para context enrichment
        - Multi-context detection (e.g., "finanzas y salud")
    """
    try:
        # Obtener último mensaje del usuario
        if not state["messages"]:
            print("[ROUTER LOG] No messages in state, defaulting to 'general'")
            return {"current_context": "general"}
        
        last_message = state["messages"][-1]
        
        # Extraer contenido de texto
        if isinstance(last_message, HumanMessage):
            user_text = last_message.content.lower()
        else:
            user_text = str(last_message.content).lower()
        
        print(f"[ROUTER LOG] Analyzing message: {user_text[:50]}...")
        
        # Keywords para cada contexto (definido por dominio)
        finance_keywords = [
            "dinero", "gasto", "presupuesto", "gastos", "financiero",
            "salario", "ingresos", "presupuesto", "tarjeta", "banco",
            "balance", "cuenta", "pago", "factura", "deuda", "costo",
        ]
        
        health_keywords = [
            "ejercicio", "hábito", "salud", "gym", "deporte", "médico",
            "medicina", "ejercitar", "correr", "caminar", "yoga", "meditación",
            "hábitos", "rutina", "entrenamiento", "actividad", "peso",
        ]
        
        docs_keywords = [
            "documento", "contrato", "póliza", "información", "buscar",
            "seguro", "archivo", "plan", "calendario", "fecha", "emergencia",
            "contacto", "teléfono", "dirección", "referencia", "consultá",
        ]
        
        # Keywords para Google Drive (MCP)
        drive_keywords = [
            "google drive", "drive", "archivo", "carpeta", "cloud", "adjunto",
            "descargar", "compartido", "fotos", "documentos", "nube", "guardar",
            "drive compartido", "mi drive", "archivo en la nube",
        ]
        
        # Contar coincidencias
        finance_score = sum(1 for kw in finance_keywords if kw in user_text)
        health_score = sum(1 for kw in health_keywords if kw in user_text)
        docs_score = sum(1 for kw in docs_keywords if kw in user_text)
        drive_score = sum(1 for kw in drive_keywords if kw in user_text)
        
        print(
            f"[ROUTER LOG] Scores - Finance: {finance_score}, "
            f"Health: {health_score}, Docs: {docs_score}, Drive: {drive_score}"
        )
        
        # Determinar contexto según puntuación
        if drive_score > finance_score and drive_score > health_score and drive_score > docs_score and drive_score > 0:
            context = "drive"
        elif finance_score > health_score and finance_score > docs_score and finance_score > 0:
            context = "finance"
        elif health_score > docs_score and health_score > 0:
            context = "health"
        elif docs_score > 0:
            context = "docs"
        else:
            context = "general"
        
        print(f"[ROUTER LOG] Context determined: {context}")
        return {"current_context": context}
        
    except Exception as e:
        print(f"[ROUTER LOG] Error in routing: {str(e)}")
        return {"current_context": "general"}


# =============================================================================
# NODE: FINANCE SPECIALIST
# =============================================================================

def finance_node(state: AgentState, llm: ChatOpenAI) -> dict:
    """
    Nodo especialista en finanzas: Usa herramientas de finanzas.
    
    Este nodo:
    1. Vincula las finance_tools al LLM
    2. Inyecta un System Prompt especializado en finanzas
    3. Incluye los active_goals del usuario
    4. Invoca el LLM y retorna la respuesta
    
    System Prompt enfatiza:
    - Experto financiero
    - Análisis de gastos y presupuestos
    - Recomendaciones personalizadas según goals
    
    Args:
        state: AgentState con mensajes y goals
        llm: Instancia de ChatOpenAI
        
    Returns:
        dict con {"messages": [AIMessage]} - mensaje de respuesta del LLM
    """
    try:
        print("[FINANCE NODE LOG] Iniciando nodo de finanzas")
        
        # Vincular herramientas al LLM
        llm_with_tools = llm.bind_tools(finance_tools)
        print(f"[FINANCE NODE LOG] Herramientas vinculadas: {len(finance_tools)}")
        
        # Construir System Prompt
        goals_text = ", ".join([f"{g.name} (meta: {g.target})" for g in state.get("active_goals", [])])
        if not goals_text:
            goals_text = "No goals defined yet"
        
        system_prompt = (
            "Eres un experto financiero especializado en gestión de presupuestos familiares.\n"
            "Tu objetivo es ayudar al usuario a optimizar sus finanzas, controlar gastos y alcanzar sus metas.\n"
            f"Metas activas del usuario: {goals_text}\n"
            "\n"
            "Cuando el usuario pregunte sobre finanzas:\n"
            "1. Usa las herramientas disponibles para obtener datos actuales\n"
            "2. Proporciona análisis detallado\n"
            "3. Ofrece recomendaciones personalizadas\n"
            "4. Sé proactivo en alertar sobre presupuestos excedidos\n"
            "5. Celebra los logros financieros\n"
            "\n"
            "Mantén un tono profesional pero accesible."
        )
        
        # Preparar mensajes para el LLM
        messages = [
            SystemMessage(content=system_prompt),
        ] + state["messages"]
        
        # Invocar LLM
        print("[FINANCE NODE LOG] Invocando LLM con herramientas...")
        response = llm_with_tools.invoke(messages)
        
        print(f"[FINANCE NODE LOG] Respuesta recibida: {type(response).__name__}")
        
        # Retornar mensaje de IA
        return {"messages": [response]}
        
    except Exception as e:
        error_msg = f"❌ Error en finance_node: {str(e)}"
        print(f"[FINANCE NODE LOG] {error_msg}")
        return {"messages": [AIMessage(content=error_msg)]}


# =============================================================================
# NODE: HEALTH SPECIALIST
# =============================================================================

def health_node(state: AgentState, llm: ChatOpenAI) -> dict:
    """
    Nodo especialista en salud: Usa herramientas de hábitos y bienestar.
    
    Este nodo:
    1. Vincula las health_tools al LLM
    2. Inyecta un System Prompt de coach de salud
    3. Incluye contexto de objetivos de salud
    4. Invoca el LLM
    
    System Prompt enfatiza:
    - Coach de salud y bienestar
    - Motivación y seguimiento de hábitos
    - Tracking de progreso
    - Recomendaciones personalizadas
    
    Args:
        state: AgentState
        llm: ChatOpenAI instance
        
    Returns:
        dict con {"messages": [AIMessage]}
    """
    try:
        print("[HEALTH NODE LOG] Iniciando nodo de salud")
        
        # Vincular herramientas
        llm_with_tools = llm.bind_tools(health_tools)
        print(f"[HEALTH NODE LOG] Herramientas vinculadas: {len(health_tools)}")
        
        # System Prompt
        system_prompt = (
            "Eres un coach de salud y bienestar especializado en hábitos familiares.\n"
            "Tu objetivo es motivar y apoyar al usuario en su camino hacia una vida más saludable.\n"
            "\n"
            "Cuando el usuario pregunte sobre salud, hábitos o ejercicio:\n"
            "1. Usa las herramientas para registrar o consultar hábitos\n"
            "2. Proporciona motivación y celebra los logros\n"
            "3. Ofrece consejos prácticos basados en progreso actual\n"
            "4. Identifica patrones y áreas de mejora\n"
            "5. Sé empático y comprensivo con los desafíos\n"
            "\n"
            "Tono: Motivador, positivo, accesible."
        )
        
        # Preparar mensajes
        messages = [
            SystemMessage(content=system_prompt),
        ] + state["messages"]
        
        # Invocar LLM
        print("[HEALTH NODE LOG] Invocando LLM con herramientas...")
        response = llm_with_tools.invoke(messages)
        
        print(f"[HEALTH NODE LOG] Respuesta recibida: {type(response).__name__}")
        
        return {"messages": [response]}
        
    except Exception as e:
        error_msg = f"❌ Error en health_node: {str(e)}"
        print(f"[HEALTH NODE LOG] {error_msg}")
        return {"messages": [AIMessage(content=error_msg)]}


# =============================================================================
# NODE: DOCUMENTS SPECIALIST
# =============================================================================

def docs_node(state: AgentState, llm: ChatOpenAI, rag_graph: Any = None) -> dict:
    """
    Nodo especialista en documentos: Usa Agentic RAG sub-grafo.
    
    Este nodo implementa el patrón "Agentic RAG" (Retrieve -> Grade -> Rewrite -> Generate)
    replicado de 3_Chat_with_your_Data.py para procesamiento inteligente de documentos.
    
    Arquitectura del RAG:
    
        Retrieve: Busca documentos en la BD
            ↓
        Grade: Valida si son relevantes (LLM)
            ↓ (condicional)
        ├─→ Generate: Si son relevantes → respuesta final
        └─→ Rewrite: Si no son relevantes → reformula pregunta
                ↓
            Retrieve: Intenta de nuevo (máx 3 loops)
    
    Este nodo:
    1. Extrae la pregunta del usuario del último mensaje
    2. Compila el RAG graph si no existe
    3. Invoca el RAG graph con la pregunta
    4. Retorna la respuesta generada (después de Retrieve/Grade/Rewrite cycle)
    
    Ventajas del Agentic RAG:
    - Valida relevancia de documentos (no devuelve cualquier cosa)
    - Reformula preguntas automáticamente si los docs no son relevantes
    - Limita loops para evitar bucles infinitos (máx 3)
    - Logging detallado de cada paso (Retrieve, Grade, Rewrite, Generate)
    
    Args:
        state: AgentState con messages, user_id, active_goals, etc.
        llm: ChatOpenAI instance
        rag_graph: CompiledStateGraph RAG (opcional, se compila si no existe)
        
    Returns:
        dict con {"messages": [AIMessage]} y contexto actualizado
    """
    try:
        print("[DOCS NODE LOG] ★ Iniciando nodo de documentos (Agentic RAG)")
        
        # 1. Extraer pregunta del usuario
        if not state["messages"]:
            print("[DOCS NODE LOG] ⚠️ No messages, retornando respuesta genérica")
            return {
                "messages": [AIMessage(content="Por favor, cuéntame qué información de documentos necesitas.")]
            }
        
        last_message = state["messages"][-1]
        if isinstance(last_message, HumanMessage):
            user_question = last_message.content
        else:
            user_question = str(last_message.content)
        
        print(f"[DOCS NODE LOG] 📝 Pregunta del usuario: '{user_question}'")
        
        # 2. Compilar RAG graph si no existe
        if rag_graph is None:
            print("[DOCS NODE LOG] 🔄 Compilando RAG sub-grafo...")
            rag_graph = compile_rag_graph(llm, retrieve_documents)
            print("[DOCS NODE LOG] ✅ RAG sub-grafo compilado")
        
        # 3. Crear estado inicial para RAG
        rag_state = create_initial_rag_state(question=user_question, max_loops=3)
        print(f"[DOCS NODE LOG] 🚀 Invocando RAG graph (max_loops=3)")
        
        # 4. Invocar RAG graph
        result = rag_graph.invoke(rag_state)
        
        # 5. Extraer respuesta generada
        final_response = result.get("generation", "No se pudo generar respuesta.")
        
        print(f"[DOCS NODE LOG] ✅ RAG graph completado")
        print(f"[DOCS NODE LOG] 📤 Respuesta generada: {len(final_response)} caracteres")
        print(f"[DOCS NODE LOG] 📊 Loops ejecutados: {result.get('loop_count', 0)}")
        
        # 6. Retornar respuesta como AIMessage
        response_msg = AIMessage(content=final_response)
        
        return {
            "messages": [response_msg],
            "current_context": "docs"
        }
        
    except Exception as e:
        error_msg = f"❌ Error en docs_node (Agentic RAG): {str(e)}"
        print(f"[DOCS NODE LOG] {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "messages": [AIMessage(content=error_msg)],
            "current_context": "docs"
        }


# =============================================================================
# NODE: GOOGLE DRIVE (MCP)
# =============================================================================

def drive_node(state: AgentState, llm: ChatOpenAI) -> dict:
    """
    Nodo especialista en Google Drive: Acceso a archivos vía MCP.
    
    Este nodo:
    1. Carga herramientas dinámicamente desde servidor MCP
    2. Vincula herramientas de Google Drive al LLM
    3. Inyecta un System Prompt especializado en archivos
    4. Maneja errores con fallback a mock si MCP no está disponible
    
    Patrón Replicado: 4_MCP_Agent.py (líneas 131-138)
    - MultiServerMCPClient para conexión
    - Carga dinámicas de herramientas
    - Manejo async con asyncio
    
    System Prompt enfatiza:
    - Acceso a Google Drive
    - Listado y lectura de archivos
    - Búsqueda en contenido
    
    Args:
        state: AgentState
        llm: ChatOpenAI instance
        
    Returns:
        dict con {"messages": [AIMessage]} y contexto actualizado
    """
    try:
        print("[DRIVE NODE LOG] ★ Iniciando nodo de Google Drive (MCP)")
        
        # Importar funciones MCP
        from src.tools.drive_mcp import create_drive_tools_mock
        import asyncio
        
        # Cargar herramientas de MCP
        print("[DRIVE NODE LOG] 📥 Cargando herramientas de MCP...")
        
        # Usar mock por defecto (fallback si MCP no está disponible)
        # En producción, podrías intentar conectar a un servidor real primero
        drive_tools = create_drive_tools_mock()
        
        print(f"[DRIVE NODE LOG] ✅ {len(drive_tools)} herramientas de Google Drive cargadas")
        
        # Vincular herramientas
        llm_with_tools = llm.bind_tools(drive_tools)
        print(f"[DRIVE NODE LOG] Herramientas vinculadas al LLM")
        
        # System Prompt
        system_prompt = (
            "Eres un especialista en gestión de archivos de Google Drive.\n"
            "Tu objetivo es ayudar al usuario a acceder, listar y leer archivos.\n"
            "\n"
            "Cuando el usuario pregunte por archivos o carpetas:\n"
            "1. Usa list_drive_files para explorar la estructura\n"
            "2. Usa read_drive_file para acceder al contenido\n"
            "3. Presenta la información de forma clara y organizada\n"
            "4. Ofrece sugerencias de navegación si es relevante\n"
            "\n"
            "Tono: Profesional, colaborativo, eficiente."
        )
        
        # Preparar mensajes
        messages = [
            SystemMessage(content=system_prompt),
        ] + state["messages"]
        
        # Invocar LLM
        print("[DRIVE NODE LOG] Invocando LLM con herramientas de MCP...")
        response = llm_with_tools.invoke(messages)
        
        print(f"[DRIVE NODE LOG] Respuesta recibida: {type(response).__name__}")
        
        return {
            "messages": [response],
            "current_context": "drive"
        }
        
    except Exception as e:
        error_msg = f"❌ Error en drive_node (MCP): {str(e)}"
        print(f"[DRIVE NODE LOG] {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "messages": [AIMessage(content=error_msg)],
            "current_context": "drive"
        }


# =============================================================================
# NODE: GENERAL CHAT
# =============================================================================

def general_node(state: AgentState, llm: ChatOpenAI) -> dict:
    """
    Nodo general: Charla casual sin herramientas especializadas.
    
    Este nodo:
    1. No vincula herramientas
    2. Usa un System Prompt general y amigable
    3. Para preguntas fuera de los dominios especializados
    
    System Prompt:
    - Asistente amigable y conversacional
    - Capaz de charla general
    - Puede sugerir derivar a especialista si es necesario
    
    Args:
        state: AgentState
        llm: ChatOpenAI instance
        
    Returns:
        dict con {"messages": [AIMessage]}
    """
    try:
        print("[GENERAL NODE LOG] Iniciando nodo general")
        
        # NO vincular herramientas - solo LLM base
        system_prompt = (
            "Eres un asistente familiar amigable y conversacional.\n"
            "Tu objetivo es ser útil, empático y accesible en conversaciones generales.\n"
            "\n"
            "Puedes:\n"
            "1. Responder preguntas generales\n"
            "2. Proporcionar información general\n"
            "3. Ser conversacional y agradable\n"
            "4. Sugerir derivar a especialistas (finanzas, salud, documentos) si es necesario\n"
            "\n"
            "Tono: Amigable, accesible, servicial."
        )
        
        # Preparar mensajes
        messages = [
            SystemMessage(content=system_prompt),
        ] + state["messages"]
        
        # Invocar LLM (sin herramientas)
        print("[GENERAL NODE LOG] Invocando LLM...")
        response = llm.invoke(messages)
        
        print(f"[GENERAL NODE LOG] Respuesta recibida: {type(response).__name__}")
        
        return {"messages": [response]}
        
    except Exception as e:
        error_msg = f"❌ Error en general_node: {str(e)}"
        print(f"[GENERAL NODE LOG] {error_msg}")
        return {"messages": [AIMessage(content=error_msg)]}


# =============================================================================
# CONDITIONAL EDGE FUNCTION
# =============================================================================

def route_based_on_context(state: AgentState) -> Literal["finance", "health", "docs", "drive", "general"]:
    """
    Función condicional que determina hacia cuál nodo enrutar.
    
    Se ejecuta después del router_node para dirigir el flujo
    al nodo especialista correcto.
    
    Args:
        state: AgentState con current_context establecido
        
    Returns:
        str con el nombre del siguiente nodo
    """
    context = state.get("current_context", "general")
    print(f"[ROUTING LOG] Enrutando a nodo: {context}")
    return context


# =============================================================================
# WORKFLOW BUILDER
# =============================================================================

def build_workflow(llm: ChatOpenAI = None):
    """
    Construye el StateGraph principal del agente.
    
    Pasos:
    1. Inicializa StateGraph con AgentState
    2. Compila el sub-grafo RAG Agentic
    3. Agrega todos los nodos
    4. Define START -> router_node
    5. Define router_node -> conditional edges
    6. Define todos los nodos -> END
    7. Compila el grafo
    
    Args:
        llm: Instancia de ChatOpenAI (si None, se crea una)
        
    Returns:
        CompiledStateGraph - Grafo compilado listo para invocar
        
    Raises:
        ValueError: Si no hay OPENAI_API_KEY configurada
    """
    
    # Inicializar LLM si no se proporciona
    if llm is None:
        print("[GRAPH LOG] Inicializando LLM...")
        llm = _get_llm()
    
    print("[GRAPH LOG] Construyendo StateGraph...")
    
    # ✨ NUEVA LÍNEA: Compilar sub-grafo RAG
    print("[GRAPH LOG] ✨ Compilando sub-grafo Agentic RAG...")
    rag_graph = compile_rag_graph(llm, retrieve_documents)
    print("[GRAPH LOG] ✨ Sub-grafo RAG listo")
    
    # 1. Crear StateGraph
    workflow = StateGraph(AgentState)
    
    # 2. Agregar nodos
    # Nota: Los nodos que requieren 'llm' son wrapeados con lambda para partial
    workflow.add_node("router", router_node)
    workflow.add_node("finance", lambda state: finance_node(state, llm))
    workflow.add_node("health", lambda state: health_node(state, llm))
    workflow.add_node("docs", lambda state: docs_node(state, llm, rag_graph))  # ✨ PASAR rag_graph
    workflow.add_node("drive", lambda state: drive_node(state, llm))  # 🔧 MCP DRIVE NODE
    workflow.add_node("general", lambda state: general_node(state, llm))
    
    print("[GRAPH LOG] Nodos agregados: router, finance, health, docs (con RAG), drive (MCP), general")
    
    # 3. Definir START -> router
    workflow.add_edge(START, "router")
    print("[GRAPH LOG] Edge agregado: START -> router")
    
    # 4. Definir conditional edges desde router
    workflow.add_conditional_edges(
        "router",
        route_based_on_context,
        {
            "finance": "finance",
            "health": "health",
            "docs": "docs",
            "drive": "drive",  # 🔧 MCP DRIVE ROUTING
            "general": "general",
        },
    )
    print("[GRAPH LOG] Conditional edges agregados desde router")
    
    # 5. Definir todos los nodos especializados -> END
    workflow.add_edge("finance", END)
    workflow.add_edge("health", END)
    workflow.add_edge("docs", END)
    workflow.add_edge("drive", END)  # 🔧 MCP DRIVE NODE -> END
    workflow.add_edge("general", END)
    print("[GRAPH LOG] Edges agregados: todos los nodos -> END")
    
    # 6. Compilar
    print("[GRAPH LOG] Compilando workflow...")
    graph = workflow.compile()
    
    print("[GRAPH LOG] ✅ StateGraph compilado exitosamente")
    return graph


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "router_node",
    "finance_node",
    "health_node",
    "docs_node",
    "drive_node",  # 🔧 MCP DRIVE NODE
    "general_node",
    "route_based_on_context",
    "build_workflow",
    "_get_llm",
]


# =============================================================================
# DEBUG / TESTING (Opcional)
# =============================================================================

if __name__ == "__main__":
    """
    Script de testing para validar el grafo.
    
    Nota: Requiere OPENAI_API_KEY en environment.
    """
    
    import os
    from src.state import create_initial_state
    
    print("\n" + "="*70)
    print("TESTING STATE GRAPH")
    print("="*70 + "\n")
    
    # Verificar API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY no configurada")
        print("   Configura: export OPENAI_API_KEY='sk-...'")
        exit(1)
    
    print("✅ API Key encontrada")
    
    try:
        # 1. Construir workflow
        print("\n1️⃣ Construyendo workflow...")
        graph = build_workflow()
        
        # 2. Crear estado inicial
        print("2️⃣ Creando estado inicial...")
        initial_state = create_initial_state(
            user_id="test-user-001",
            user_name="Test User",
        )
        
        # 3. Agregar mensaje de prueba
        print("3️⃣ Agregando mensaje de prueba...")
        initial_state["messages"] = [
            HumanMessage(content="¿Cuál es mi presupuesto de este mes?")
        ]
        
        # 4. Invocar grafo
        print("4️⃣ Invocando grafo...")
        result = graph.invoke(initial_state)
        
        print("\n✅ Resultado:")
        print(f"   Current Context: {result.get('current_context')}")
        print(f"   Messages: {len(result.get('messages', []))} mensajes")
        
        if result.get("messages"):
            last_msg = result["messages"][-1]
            content = last_msg.content[:100] if hasattr(last_msg, "content") else str(last_msg)[:100]
            print(f"   Última respuesta: {content}...")
        
        print("\n" + "="*70)
        print("✅ Test completado!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error durante testing: {str(e)}")
        import traceback
        traceback.print_exc()
