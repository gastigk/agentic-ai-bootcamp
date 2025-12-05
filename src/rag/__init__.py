"""
Agentic RAG Package
===================

Módulo de sub-grafo RAG para procesamiento inteligente de documentos
usando el patrón Retrieve -> Grade -> Rewrite -> Generate.

Public API:
  • compile_rag_graph(llm, retrieve_tool): Compila el sub-grafo
  • create_initial_rag_state(question, max_loops): Estado inicial
  • RAGState: TypedDict del estado RAG

Ejemplo de uso:
  
  from src.rag import compile_rag_graph, create_initial_rag_state
  from src.tools.docs import retrieve_documents
  from langchain_openai import ChatOpenAI
  
  llm = ChatOpenAI(model="gpt-4o-mini")
  rag_graph = compile_rag_graph(llm, retrieve_documents)
  
  state = create_initial_rag_state(question="¿Dónde está mi póliza?")
  result = rag_graph.invoke(state)
  print(result["generation"])  # Respuesta final
"""

from src.rag.graph import (
    RAGState,
    compile_rag_graph,
    create_initial_rag_state,
    retrieve_node,
    grade_node,
    rewrite_node,
    generate_node,
)

__all__ = [
    "RAGState",
    "compile_rag_graph",
    "create_initial_rag_state",
    "retrieve_node",
    "grade_node",
    "rewrite_node",
    "generate_node",
]
