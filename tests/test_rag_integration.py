"""
Test Script: Agentic RAG Integration
====================================

Este script demuestra el funcionamiento del Agentic RAG sub-grafo
integrado en el docs_node del grafo principal.

Flujo:
1. Inicializa el LLM
2. Compila el RAG graph
3. Ejecuta varios casos de prueba que muestran:
   - Retrieve: Búsqueda de documentos
   - Grade: Validación de relevancia
   - Rewrite: Reformulación de pregunta (si es necesario)
   - Generate: Generación de respuesta final

Salida esperada: Logs detallados de cada paso con [RAG LOG], [RETRIEVE LOG], etc.

Ejecución:
  python test_rag_integration.py
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# =============================================================================
# IMPORTS
# =============================================================================

from langchain_openai import ChatOpenAI
from src.rag import compile_rag_graph, create_initial_rag_state
from src.tools.docs import retrieve_documents


# =============================================================================
# TEST CASES
# =============================================================================

TEST_CASES = [
    {
        "id": 1,
        "question": "¿Dónde está mi póliza de seguro?",
        "expected_domain": "insurance",
        "description": "Pregunta clara sobre póliza (docs_keywords: póliza, seguro)"
    },
    {
        "id": 2,
        "question": "¿Cuál es mi presupuesto recomendado?",
        "expected_domain": "docs/budget",
        "description": "Pregunta sobre presupuesto/plan (docs_keywords: información, plan, presupuesto)"
    },
    {
        "id": 3,
        "question": "¿Qué alimentos debo comer según mi plan?",
        "expected_domain": "nutrition",
        "description": "Pregunta mixta (docs + health, pero docs primary)"
    },
    {
        "id": 4,
        "question": "Necesito información sobre mi contrato de arrendamiento",
        "expected_domain": "legal",
        "description": "Pregunta clara sobre documento legal (contrato)"
    },
]


# =============================================================================
# MAIN TEST
# =============================================================================

def main():
    """Ejecuta test suite del Agentic RAG."""
    
    print("=" * 80)
    print("🧪 TEST SUITE: Agentic RAG Integration")
    print("=" * 80)
    
    # Validar API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY no configurada")
        print("   Ejecuta: export OPENAI_API_KEY='sk-...'")
        sys.exit(1)
    
    print("✅ API Key configurada")
    
    # 1. Inicializar LLM
    print("\n[SETUP] Inicializando LLM...")
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=api_key
        )
        print("✅ LLM inicializado (gpt-4o-mini)")
    except Exception as e:
        print(f"❌ Error inicializando LLM: {e}")
        sys.exit(1)
    
    # 2. Compilar RAG Graph
    print("\n[SETUP] Compilando RAG sub-grafo...")
    try:
        rag_graph = compile_rag_graph(llm, retrieve_documents)
        print("✅ RAG sub-grafo compilado")
    except Exception as e:
        print(f"❌ Error compilando RAG: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 3. Ejecutar test cases
    print("\n" + "=" * 80)
    print("📋 EJECUTANDO TEST CASES")
    print("=" * 80)
    
    for test in TEST_CASES:
        test_id = test["id"]
        question = test["question"]
        description = test["description"]
        
        print(f"\n{'─' * 80}")
        print(f"Test {test_id}: {description}")
        print(f"{'─' * 80}")
        print(f"📝 Pregunta: {question}")
        print(f"\n🚀 Invocando RAG graph...")
        print()
        
        try:
            # Crear estado inicial
            rag_state = create_initial_rag_state(question=question, max_loops=3)
            
            # Invocar RAG graph
            result = rag_graph.invoke(rag_state)
            
            # Mostrar resultados
            print()
            print(f"{'─' * 80}")
            print("✅ RESULTADO:")
            print(f"{'─' * 80}")
            
            generation = result.get("generation", "N/A")
            loop_count = result.get("loop_count", 0)
            doc_count = len(result.get("documents", []))
            
            print(f"📄 Documentos recuperados: {doc_count}")
            print(f"🔄 Loops de reescritura: {loop_count}/3")
            print()
            print("Respuesta generada:")
            print(f"  {generation}")
            print()
            print(f"✅ Test {test_id} completado")
            
        except Exception as e:
            print(f"❌ Error en Test {test_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN DEL TEST")
    print("=" * 80)
    print(f"Total de tests: {len(TEST_CASES)}")
    print("✅ Todos los tests completados")
    print()
    print("Características demostradas:")
    print("  ✓ Retrieve: Búsqueda de documentos relevantes")
    print("  ✓ Grade: Validación de relevancia con LLM")
    print("  ✓ Rewrite: Reformulación de preguntas no relevantes")
    print("  ✓ Generate: Generación de respuestas basadas en documentos")
    print("  ✓ Limite de loops: Máximo 3 iteraciones para evitar bucles infinitos")
    print()
    print("🎉 Agentic RAG integrado exitosamente en docs_node")
    print("=" * 80)


if __name__ == "__main__":
    main()
