"""
Family AI Assistant - Main Streamlit App
==========================================

Entry point de la aplicación. Implementa la interfaz de chat siguiendo
el patrón de Home.py del bootcamp, pero optimizado para Mobile-First.

Responsabilidades:
1. Configurar la página para móviles (st.set_page_config)
2. Gestionar API keys via st.secrets + fallback manual
3. Cargar mock data de objetivos (pronto conectaremos PostgreSQL)
4. Renderizar chat interactivo (st.chat_message)
5. Llamar al grafo LangGraph compilado (próximamente en src/graph.py)

Flujo:
    Usuario escribe en chat_input
        ↓
    Se agrega a st.session_state.messages
        ↓
    Se pasa a graph.invoke(state) [PRÓXIMA TAREA]
        ↓
    Se renderiza respuesta + reasoning_steps en expander
"""

# =============================================================================
# IMPORTS
# =============================================================================

import streamlit as st
import uuid
from datetime import datetime
from typing import Optional, List

# Nuestro módulo de estado (src/state.py)
from src.state import AgentState, Goal, create_initial_state

# Grafo LangGraph (src/graph.py)
from src.graph import build_workflow

# LangChain
from langchain_core.messages import HumanMessage


# =============================================================================
# PAGE CONFIGURATION (Mobile-First)
# =============================================================================

st.set_page_config(
    page_title="👨‍👩‍👧‍👦 Family AI Assistant",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",  # Ancho completo, responsive en móvil
    initial_sidebar_state="collapsed",  # En móvil, el sidebar debe estar colapsado por defecto
)

st.title("👨‍👩‍👧‍👦 Family AI Assistant")
st.caption("Your personal AI for finances, habits, and documents")


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

# ========== API Keys & LLM ==========
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""
    """Clave de OpenAI (desde st.secrets o input manual)"""

if "llm" not in st.session_state:
    st.session_state.llm = None
    """Instancia de ChatOpenAI (inicializada cuando hay clave)"""

# ========== User Context ==========
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
    """ID único para el usuario (simula login; usar DB en producción)"""

if "user_goals" not in st.session_state:
    st.session_state.user_goals = []
    """Lista de Goal objects cargados de PostgreSQL (mock data por ahora)"""

if "agent_state" not in st.session_state:
    # Inicializar AgentState con estado vacío
    st.session_state.agent_state = create_initial_state(
        user_id=st.session_state.user_id,
        goals=st.session_state.user_goals,
    )
    """Estado central del grafo LangGraph (referencia: src/state.py)"""

# ========== Chat & Workflow ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    """Historial de chat visible en la UI (sync con agent_state.messages)"""

if "workflow" not in st.session_state:
    st.session_state.workflow = None
    """Instancia compilada de StateGraph (se crea en src/graph.py)"""

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    """ID de sesión para tracking y debugging"""


# =============================================================================
# SIDEBAR: API KEYS & CONFIGURATION
# =============================================================================

with st.sidebar:
    st.subheader("🔑 Settings")

    # ========== API Key Status ==========
    if st.session_state.openai_key:
        st.success("✅ OpenAI Connected")
    else:
        st.warning("⚠️ OpenAI Not Connected")

    st.divider()

    # ========== User Info ==========
    st.subheader("👤 User Info")
    st.caption(f"ID: `{st.session_state.user_id[:8]}...`")
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")

    st.divider()

    # ========== Active Goals (Mock Data for now) ==========
    st.subheader("🎯 Active Goals")
    if st.session_state.user_goals:
        for goal in st.session_state.user_goals:
            progress = (goal.current / goal.target * 100) if goal.target > 0 else 0
            st.metric(
                label=f"{goal.name}",
                value=f"{goal.current}/{goal.target}",
                help=f"Unit: {goal.unit} | Deadline: {goal.deadline or 'N/A'}",
            )
            st.progress(progress / 100)
    else:
        st.info("No goals loaded yet. Mock data will be added below.")

    st.divider()

    # ========== Mock Goals Button (Simulates DB load) ==========
    if st.button("📥 Load Mock Goals (Simulates DB)", use_container_width=True):
        """
        Simula cargar objetivos de PostgreSQL.
        En el siguiente sprint, reemplazaremos esto con:
            goals = load_goals_from_db(user_id)
        """
        st.session_state.user_goals = [
            Goal(
                name="ahorro",
                target=500,
                current=150,
                unit="USD",
                deadline="2025-12-31",
            ),
            Goal(
                name="gym",
                target=12,
                current=4,
                unit="veces",
                deadline="2025-12-31",
            ),
            Goal(
                name="lectura",
                target=4,
                current=1,
                unit="libros",
                deadline="2025-12-31",
            ),
        ]
        st.session_state.agent_state["active_goals"] = {
            g.name: g for g in st.session_state.user_goals
        }
        st.success("✅ Mock goals loaded")
        st.rerun()

    st.divider()

    # ========== Change API Keys Button ==========
    if st.session_state.openai_key:
        if st.button("🔄 Change API Key", use_container_width=True):
            st.session_state.openai_key = ""
            st.session_state.llm = None
            st.rerun()


# =============================================================================
# API KEY INPUT (If not already set)
# =============================================================================

if not st.session_state.openai_key:
    st.info("ℹ️ To get started, provide an OpenAI API key.")

    # Try to load from st.secrets first
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
        if secret_key and secret_key.startswith("sk-"):
            st.session_state.openai_key = secret_key
            st.success("✅ API key loaded from secrets")
            st.rerun()
    except (FileNotFoundError, KeyError):
        pass

    # If not in secrets, ask user manually
    api_key = st.text_input(
        "🔐 OpenAI API Key",
        type="password",
        placeholder="sk-proj-...",
        help="Get one from https://platform.openai.com/api-keys",
    )

    if st.button("Connect", use_container_width=True):
        if api_key and api_key.startswith("sk-"):
            st.session_state.openai_key = api_key
            st.rerun()
        else:
            st.error("❌ Invalid API key format. Must start with 'sk-'")

    st.stop()  # No mostrar resto de app hasta conectar


# =============================================================================
# INITIALIZE LLM (if not already done)
# =============================================================================

if not st.session_state.llm:
    from langchain_openai import ChatOpenAI

    st.session_state.llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=st.session_state.openai_key,
    )
    st.rerun()  # Reiniciar para preparar el grafo


# =============================================================================
# BUILD WORKFLOW (Referencia: 1_Basic_Chatbot.py)
# =============================================================================

if st.session_state.llm and not st.session_state.workflow:
    try:
        print("✅ [APP LOG] Inicializando workflow...")
        st.session_state.workflow = build_workflow(st.session_state.llm)
        print("✅ [APP LOG] Workflow inicializado exitosamente")
        st.success("✅ Graph initialized and ready!")
    except Exception as e:
        st.error(f"❌ Error initializing workflow: {str(e)}")
        print(f"❌ [APP LOG] Error: {str(e)}")
        st.stop()


# =============================================================================
# MAIN CHAT INTERFACE
# =============================================================================

st.divider()

# ========== Display Chat History ==========
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# ========== Chat Input (Bottom) ==========
user_input = st.chat_input(
    "Ask me anything... 💬",
    key="chat_input",
)

if user_input:
    # 1. Agregar mensaje del usuario al historial visual
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat(),
        }
    )

    # 2. Crear mensaje de LangChain
    human_msg = HumanMessage(content=user_input)
    
    # 3. Invocar al Grafo con UI feedback
    with st.chat_message("assistant"):
        with st.spinner("🤔 Pensando..."):
            try:
                print(f"[APP LOG] Procesando entrada del usuario: {user_input[:50]}...")
                
                # Prepara el estado actual
                current_state = st.session_state.agent_state.copy()
                current_state["messages"].append(human_msg)
                
                print(f"[APP LOG] Estado preparado. Invocando workflow...")
                
                # INVOKE - La magia sucede aquí
                result = st.session_state.workflow.invoke(current_state)
                
                print(f"[APP LOG] Workflow ejecutado. Procesando resultado...")
                
                # Actualiza el estado global con el resultado completo
                st.session_state.agent_state = result
                
                # Obtener la última respuesta del AI
                last_msg = result["messages"][-1]
                response_text = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
                
                # Renderizar respuesta
                st.write(response_text)
                
                # Guardar en historial visual para renderizado posterior
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                
                print(f"[APP LOG] Respuesta procesada y guardada")
                
            except Exception as e:
                error_msg = f"❌ Error ejecutando el agente: {str(e)}"
                st.error(error_msg)
                print(f"[APP LOG] {error_msg}")
                import traceback
                print(traceback.format_exc())

    st.rerun()


# =============================================================================
# FOOTER / DEBUG INFO
# =============================================================================

st.divider()

with st.expander("🔍 Debug Info"):
    st.write("**Session ID:**", st.session_state.session_id)
    st.write("**User ID:**", st.session_state.user_id)
    st.write("**Messages in state:**", len(st.session_state.messages))
    st.write("**Active goals:**", len(st.session_state.user_goals))
    st.write("**LLM Model:**", "gpt-4o-mini" if st.session_state.llm else "Not initialized")
    st.write("**Workflow Status:**", "✅ Ready" if st.session_state.workflow else "⏳ Initializing...")
    
    if st.session_state.agent_state:
        st.write("**Current Context:**", st.session_state.agent_state.get("current_context", "unknown"))
        st.write("**Agent State Messages:**", len(st.session_state.agent_state.get("messages", [])))
    
    st.divider()
    st.caption("💡 Tip: Check terminal output for [APP LOG] debugging information")
