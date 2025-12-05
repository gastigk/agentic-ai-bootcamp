"""
Document Retrieval Tools for Family AI Assistant
=================================================

Herramientas personalizadas (@tool decorators) para la recuperación
de información en documentos familiares.

Patrón Replicado: 3_Chat_with_your_Data.py (líneas 150-220)
- Mock vector store (simula FAISS/Milvus)
- Búsqueda simple con palabras clave (próxima: embeddings reales)
- Docstrings detallados para que el router sepa cuándo usarla
- Type hints completos

Nota: Este módulo simula un vector store en memoria.
En Tarea 3, lo reemplazaremos con:
    - FAISS o Milvus para embeddings reales
    - Carga de PDFs desde el filesystem
    - Chunking de documentos
"""

# =============================================================================
# IMPORTS
# =============================================================================

from langchain_core.tools import tool
from typing import List, Optional
from difflib import SequenceMatcher


# =============================================================================
# MOCK VECTOR STORE / DOCUMENT DATABASE
# =============================================================================

# Simulación de documentos familiares en una "base de datos de documentos"
# En Tarea 3, esto será reemplazado por:
#   from src.database.vector_store import retrieve_from_milvus()

MOCK_DOCS = [
    {
        "id": 1,
        "title": "Póliza de Seguro de Auto",
        "content": (
            "Póliza de Seguro de Auto - Documento oficial\n"
            "Asegurador: Global Insurance Inc.\n"
            "Tipo de cobertura: Comprehensive + Collision\n"
            "Cubre daños a terceros hasta $50,000\n"
            "Cubre daños propios hasta $30,000\n"
            "Deducible: $500\n"
            "Vigencia: 2025-01-01 hasta 2026-01-01\n"
            "Vence: 2026-01-01\n"
            "Número de Póliza: POL-2025-AUTO-12345\n"
            "Contacto de Emergencia: 1-800-555-INSURANCE\n"
            "Procedimiento en caso de accidente:\n"
            "1. Llamar a emergencias\n"
            "2. Notificar a la aseguradora dentro de 24 horas\n"
            "3. Adjuntar documentos de soporte"
        ),
        "category": "insurance",
        "tags": ["auto", "seguro", "póliza", "cobertura", "deducible"],
    },
    {
        "id": 2,
        "title": "Plan Nutricional Familiar",
        "content": (
            "Plan de Nutrición - Programa de Salud Familiar\n"
            "Objetivo: Mantener una dieta balanceada y saludable\n"
            "\n"
            "SEMANA 1:\n"
            "Lunes: Pescado a la parrilla con vegetales, arroz integral\n"
            "Martes: Pollo al horno con batata y brócoli\n"
            "Miércoles: Pavo molido con espagueti integral\n"
            "Jueves: Salmón con quinua y espárragos\n"
            "Viernes: Pechuga de pollo con ensalada de aguacate\n"
            "Sábado: Carne magra con papas al horno\n"
            "Domingo: Descanso - comida con familia (sin restricciones)\n"
            "\n"
            "RECOMENDACIONES:\n"
            "- Evitar azúcares refinados\n"
            "- Beber 2 litros de agua diaria\n"
            "- Consumir frutas entre comidas\n"
            "- Proteína en cada comida principal\n"
            "- Grasas saludables (aguacate, nueces, aceite de oliva)\n"
            "- Evitar alimentos ultraprocesados\n"
            "- Snacks saludables: yogur, frutos secos, frutas\n"
            "\n"
            "ALERGIAS/RESTRICCIONES:\n"
            "- Ninguna reportada (revisar anualmente)"
        ),
        "category": "nutrition",
        "tags": ["dieta", "nutrición", "comida", "salud", "alimentos"],
    },
    {
        "id": 3,
        "title": "Contrato de Arrendamiento",
        "content": (
            "CONTRATO DE ARRENDAMIENTO DE INMUEBLE\n"
            "Celebrado entre:\n"
            "ARRENDADOR: Property Management Corp.\n"
            "ARRENDATARIO: Tu Familia\n"
            "\n"
            "PROPIEDADES:\n"
            "Dirección: 123 Main Street, Apartment 4B\n"
            "Tipo: Apartamento de 2 dormitorios\n"
            "\n"
            "TÉRMINOS:\n"
            "Duración: 12 meses (renovable)\n"
            "Fecha de Inicio: 2025-01-01\n"
            "Fecha de Vencimiento: 2026-01-01\n"
            "Monto de Renta: $1,200 USD mensual\n"
            "Día de Pago: Antes del día 5 de cada mes\n"
            "Forma de Pago: Transferencia bancaria\n"
            "Número de Cuenta: 123-456-789\n"
            "\n"
            "DEPÓSITO DE SEGURIDAD:\n"
            "Monto: $1,200 USD (equivalente a 1 mes)\n"
            "Estado: Depositado\n"
            "Devolución: Al finalizar contrato (menos daños)\n"
            "\n"
            "RESPONSABILIDADES DEL ARRENDATARIO:\n"
            "- Mantener el inmueble en buen estado\n"
            "- Pagar servicios (luz, agua, gas) a tiempo\n"
            "- Notificar reparaciones necesarias\n"
            "- No permitir subarrendamiento\n"
            "\n"
            "CAUSALES DE TERMINACIÓN:\n"
            "- Falta de pago por 30 días\n"
            "- Daños graves al inmueble\n"
            "- Violación de cláusulas del contrato"
        ),
        "category": "legal",
        "tags": ["arrendamiento", "renta", "contrato", "pago", "vivienda"],
    },
    {
        "id": 4,
        "title": "Rutina de Ejercicio",
        "content": (
            "RUTINA DE EJERCICIO - Programa de Fitness Familiar\n"
            "Objetivo: Mantener actividad física regular\n"
            "Duración de sesión: 45-60 minutos\n"
            "\n"
            "CALENTAMIENTO (5 minutos):\n"
            "- Caminata suave\n"
            "- Movimientos articulares dinámicos\n"
            "- Estiramientos activos\n"
            "\n"
            "ENTRENAMIENTO CARDIOVASCULAR (20 minutos):\n"
            "- Correr: 3 km\n"
            "- O trotar: 5 km\n"
            "- O bicicleta: 15 km\n"
            "- Intensidad: Moderada (60-75% FCMax)\n"
            "\n"
            "ENTRENAMIENTO DE FUERZA (20 minutos):\n"
            "Lunes: Pecho y tríceps\n"
            "Martes: Espalda y bíceps\n"
            "Miércoles: Piernas\n"
            "Jueves: Hombros y core\n"
            "Viernes: HIIT (entrenamiento de alta intensidad)\n"
            "\n"
            "ENFRIAMIENTO (5-10 minutos):\n"
            "- Caminata lenta\n"
            "- Estiramientos estáticos\n"
            "- Respiración profunda\n"
            "\n"
            "FRECUENCIA: 5 días a la semana (descanso sábado-domingo)"
        ),
        "category": "health",
        "tags": ["ejercicio", "gym", "fitness", "deporte", "rutina"],
    },
    {
        "id": 5,
        "title": "Presupuesto Mensual Familiar",
        "content": (
            "PRESUPUESTO MENSUAL FAMILIAR - 2025\n"
            "Ingresos Totales: $4,500 USD\n"
            "\n"
            "GASTOS FIJOS:\n"
            "Renta/Hipoteca: $1,200 (26.7%)\n"
            "Servicios (luz, agua, gas): $150 (3.3%)\n"
            "Internet/Telefonía: $100 (2.2%)\n"
            "Seguro de Auto: $150 (3.3%)\n"
            "Seguro de Salud: $250 (5.6%)\n"
            "Subtotal Fijos: $1,850\n"
            "\n"
            "GASTOS VARIABLES:\n"
            "Alimentos: $500 (11.1%)\n"
            "Transporte: $150 (3.3%)\n"
            "Entretenimiento: $150 (3.3%)\n"
            "Educación: $200 (4.4%)\n"
            "Ropa y Calzado: $100 (2.2%)\n"
            "Cuidados Personales: $80 (1.8%)\n"
            "Subtotal Variables: $1,180\n"
            "\n"
            "AHORRO Y METAS:\n"
            "Fondo de Emergencia: $400 (8.9%)\n"
            "Vacaciones: $200 (4.4%)\n"
            "Inversiones: $200 (4.4%)\n"
            "Subtotal Ahorro: $800\n"
            "\n"
            "TOTAL: $3,830 (Sobra: $670 - flexible para ajustes)"
        ),
        "category": "finance",
        "tags": ["presupuesto", "gastos", "finanzas", "dinero", "ingresos"],
    },
    {
        "id": 6,
        "title": "Calendario Médico y Vacunas",
        "content": (
            "CALENDARIO MÉDICO Y VACUNAS - Registro de Salud Familiar\n"
            "\n"
            "CITAS MÉDICAS:\n"
            "Juan (Padre):\n"
            "- Próximo chequeo general: 2025-02-15\n"
            "- Oftalmólogo: 2025-01-30\n"
            "- Dentista: Cada 6 meses\n"
            "\n"
            "María (Madre):\n"
            "- Próximo chequeo general: 2025-02-20\n"
            "- Ginecólogo: Anualmente\n"
            "- Dermatólogo: 2025-03-10\n"
            "\n"
            "VACUNAS:\n"
            "REQUERIDAS:\n"
            "- COVID-19: Completar dosis (cada 1 año)\n"
            "- Influenza (Gripe): Anual (Octubre-Noviembre)\n"
            "- Neumococo: Cada 5 años\n"
            "- Tétanos: Cada 10 años\n"
            "\n"
            "RECOMENDADAS:\n"
            "- Shingles (Herpes Zóster): Mayores de 50 años\n"
            "- VPH: Jóvenes (si aplica)\n"
            "\n"
            "REGISTRO DE VACUNACIÓN:\n"
            "- COVID: Última dosis 2024-11-15 (próxima: 2025-11-15)\n"
            "- Influenza: Última dosis 2024-10-20 (próxima: 2025-10-20)\n"
            "- Neumococo: Última dosis 2022-03-10 (próxima: 2027-03-10)"
        ),
        "category": "health",
        "tags": ["vacunas", "médico", "salud", "citas", "chequeo"],
    },
    {
        "id": 7,
        "title": "Números Importantes de Emergencia",
        "content": (
            "NÚMEROS IMPORTANTES DE EMERGENCIA\n"
            "\n"
            "SERVICIOS DE EMERGENCIA:\n"
            "Emergencias Médicas (Ambulancia): 911\n"
            "Bomberos: 911\n"
            "Policía: 911\n"
            "\n"
            "HOSPITALES CERCANOS:\n"
            "Hospital General: (555) 123-4567\n"
            "Clínica Privada: (555) 234-5678\n"
            "Centro Urgencias 24h: (555) 345-6789\n"
            "\n"
            "CONTACTOS MÉDICOS:\n"
            "Médico General (Dr. Smith): (555) 456-7890\n"
            "Dentista (Dra. García): (555) 567-8901\n"
            "Oftalmólogo (Dr. Brown): (555) 678-9012\n"
            "\n"
            "SERVICIOS DE UTILIDAD:\n"
            "Servicios de Gas: (555) 789-0123\n"
            "Agua y Alcantarillado: (555) 890-1234\n"
            "Electricidad: (555) 901-2345\n"
            "Internet/Telefonía: (555) 012-3456\n"
            "\n"
            "SEGUROS:\n"
            "Seguro Auto: 1-800-555-AUTO\n"
            "Seguro Salud: 1-800-555-HEALTH\n"
            "Seguro Hogar: 1-800-555-HOME\n"
            "\n"
            "CONTACTOS FAMILIARES IMPORTANTES:\n"
            "Abuelo paterno (Emergencias): (555) 111-2222\n"
            "Tía María (Respaldo): (555) 222-3333\n"
            "Primo Carlos (Soporte): (555) 333-4444"
        ),
        "category": "emergency",
        "tags": ["emergencia", "teléfono", "contacto", "hospital", "ayuda"],
    },
]
"""
Base de datos mock de documentos familiares.
Estructura: Lista de dicts con id, title, content, category, tags.
En Tarea 3: Reemplazar con carga desde PDFs + embeddings en FAISS/Milvus.
"""


# =============================================================================
# HELPER FUNCTIONS (Interno - no son tools)
# =============================================================================

def _calculate_similarity(query: str, text: str) -> float:
    """
    Calcula una puntuación simple de similitud entre query y text.
    
    Usa SequenceMatcher de difflib para una medida rápida y simple.
    En Tarea 3, usaremos embeddings reales de OpenAI.
    
    Args:
        query: Consulta del usuario
        text: Texto a comparar
        
    Returns:
        Puntuación entre 0.0 y 1.0
    """
    matcher = SequenceMatcher(None, query.lower(), text.lower())
    return matcher.ratio()


def _search_documents(query: str, top_k: int = 3) -> list:
    """
    Busca documentos relevantes usando palabras clave y similitud.
    
    Algoritmo:
    1. Tokenizar query en palabras clave
    2. Buscar en tags primero (mayor relevancia) - matching parcial
    3. Si no hay resultados, buscar en contenido
    4. Ordenar por score de relevancia
    5. Retornar top_k resultados
    
    Args:
        query: Consulta del usuario
        top_k: Número máximo de documentos a retornar
        
    Returns:
        Lista de dicts con documentos + scores
    """
    query_lower = query.lower()
    keywords = query_lower.split()
    
    results = []
    
    # Fase 1: Búsqueda por tags (mayor relevancia) - con matching parcial
    for doc in MOCK_DOCS:
        doc_tags = [tag.lower() for tag in doc.get("tags", [])]
        doc_title = doc["title"].lower()
        doc_category = doc["category"].lower()
        
        # Contar matches exactos y parciales
        tag_matches = 0
        for keyword in keywords:
            # Exact match en tags
            if keyword in doc_tags:
                tag_matches += 2  # Mayor peso para matches exactos
            # Partial match en tags (palabra contiene keyword)
            elif any(keyword in tag for tag in doc_tags):
                tag_matches += 1
            # Match en título
            elif keyword in doc_title:
                tag_matches += 1.5
            # Match en categoría
            elif keyword in doc_category:
                tag_matches += 1
        
        if tag_matches > 0:
            # Calcular score adicional por similitud del contenido
            content_score = _calculate_similarity(query, doc["content"][:300])
            total_score = (tag_matches * 0.6) + (content_score * 0.4)
            
            results.append({
                "doc": doc,
                "score": total_score,
                "reason": "tag_match",
            })
    
    # Fase 2: Búsqueda por contenido (si no hay suficientes resultados)
    if len(results) < top_k:
        for doc in MOCK_DOCS:
            # Evitar duplicados
            if any(r["doc"]["id"] == doc["id"] for r in results):
                continue
            
            # Calcular similitud con el contenido
            score = _calculate_similarity(query, doc["content"])
            
            if score > 0.15:  # Threshold mínimo más bajo
                results.append({
                    "doc": doc,
                    "score": score,
                    "reason": "content_match",
                })
    
    # Ordenar por score y retornar top_k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# =============================================================================
# TOOLS (Decoradas con @tool - Patrón Bootcamp 3)
# =============================================================================

@tool
def retrieve_documents(query: str) -> str:
    """
    Retrieve information from family documents using keyword search.
    
    This tool searches through a database of family documents such as:
    - Insurance policies (auto, health, home)
    - Nutrition and meal plans
    - Rental contracts and legal documents
    - Exercise routines and fitness plans
    - Budget spreadsheets
    - Medical records and vaccination calendars
    - Emergency contact numbers
    
    Use this tool when the user asks for document-specific information:
    - "What's my insurance coverage?"
    - "Show me my nutrition plan"
    - "When is my rent due?"
    - "What's my gym routine?"
    - "What emergency numbers do I have?"
    - "Show my medical appointments"
    
    The tool performs keyword matching in document titles, tags, and content.
    Returns the most relevant documents with similarity scores.
    
    Args:
        query: User's search query (e.g., "insurance", "nutrition plan", "rent due date")
    
    Returns:
        Formatted string with retrieved documents and relevant excerpts
    
    Example:
        >>> retrieve_documents.invoke({"query": "insurance policy coverage"})
        "📄 DOCUMENT RETRIEVAL RESULTS\n
         Found 2 documents:\n
         1. Póliza de Seguro de Auto (98% match)\n
         Cubre daños a terceros hasta $50,000..."
    """
    try:
        print(f"[TOOL LOG] retrieve_documents called: query='{query}'")
        
        # Validar entrada
        if not query or len(query.strip()) < 2:
            return "❌ Error: Query too short. Please provide at least 2 characters."
        
        # Buscar documentos
        results = _search_documents(query, top_k=3)
        
        if not results:
            print(f"[TOOL LOG] No documents found for query: {query}")
            return (
                f"📭 No relevant documents found for: '{query}'\n"
                f"Try searching for: insurance, nutrition, contract, exercise, emergency"
            )
        
        # Formatear respuesta
        output = "📄 DOCUMENT RETRIEVAL RESULTS\n" + "="*50 + "\n"
        output += f"Query: '{query}'\n"
        output += f"Found {len(results)} document(s):\n\n"
        
        for i, result in enumerate(results, 1):
            doc = result["doc"]
            score = result["score"]
            score_percent = int(score * 100)
            
            # Relevancia visual
            if score_percent >= 80:
                relevance_icon = "⭐⭐⭐"
            elif score_percent >= 60:
                relevance_icon = "⭐⭐"
            else:
                relevance_icon = "⭐"
            
            output += f"{i}. {doc['title'].upper()} {relevance_icon}\n"
            output += f"   Category: {doc['category']} | Match: {score_percent}%\n"
            output += f"   Content Preview:\n"
            
            # Mostrar preview del contenido (primeras 200 caracteres)
            preview = doc["content"][:200].strip()
            if len(doc["content"]) > 200:
                preview += "..."
            
            for line in preview.split("\n"):
                output += f"   {line}\n"
            
            output += "\n"
        
        print(f"[TOOL LOG] Retrieved {len(results)} documents")
        return output
        
    except Exception as e:
        error_msg = f"❌ Error retrieving documents: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def search_by_category(category: str) -> str:
    """
    Search for all documents in a specific category.
    
    Categories available:
    - insurance: Insurance policies and coverage details
    - nutrition: Meal plans and dietary guidelines
    - legal: Contracts and legal documents
    - health: Medical records, exercises, schedules
    - finance: Budget and financial planning
    - emergency: Emergency contacts and procedures
    
    Use this when the user wants to browse documents by type:
    - "Show me all insurance documents"
    - "List my health records"
    - "What legal documents do I have?"
    - "Show budget information"
    
    Args:
        category: Category name (insurance, nutrition, legal, health, finance, emergency)
    
    Returns:
        List of all documents in the category with previews
    
    Example:
        >>> search_by_category.invoke({"category": "insurance"})
        "Insurance Documents (1 found):\n
         • Póliza de Seguro de Auto..."
    """
    try:
        print(f"[TOOL LOG] search_by_category called: category='{category}'")
        
        category_lower = category.lower()
        
        # Buscar documentos en la categoría
        matching_docs = [doc for doc in MOCK_DOCS if doc["category"] == category_lower]
        
        if not matching_docs:
            available = ", ".join(set(doc["category"] for doc in MOCK_DOCS))
            return (
                f"❌ Category '{category}' not found.\n"
                f"Available categories: {available}"
            )
        
        output = f"📚 CATEGORY: {category_lower.upper()}\n"
        output += "="*50 + "\n"
        output += f"Found {len(matching_docs)} document(s):\n\n"
        
        for doc in matching_docs:
            output += f"📄 {doc['title']}\n"
            output += f"   Tags: {', '.join(doc['tags'])}\n"
            
            # Preview
            preview = doc["content"][:150].replace("\n", " ")
            if len(doc["content"]) > 150:
                preview += "..."
            
            output += f"   {preview}\n\n"
        
        print(f"[TOOL LOG] Found {len(matching_docs)} documents in category '{category}'")
        return output
        
    except Exception as e:
        error_msg = f"❌ Error searching by category: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def list_all_documents() -> str:
    """
    List all available documents in the database.
    
    Useful for browsing what documents are available without
    a specific search query.
    
    Use this when the user asks:
    - "What documents do I have?"
    - "Show me everything"
    - "List all documents"
    
    Returns:
        Formatted list of all documents with categories
    
    Example:
        >>> list_all_documents.invoke({})
        "FAMILY DOCUMENT DATABASE\n
         Total: 7 documents\n
         Categories:\n
         • Insurance (1)\n
         • Nutrition (1)\n
         • Legal (1)\n..."
    """
    try:
        print(f"[TOOL LOG] list_all_documents called")
        
        # Agrupar por categoría
        by_category = {}
        for doc in MOCK_DOCS:
            cat = doc["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(doc)
        
        output = "📚 FAMILY DOCUMENT DATABASE\n"
        output += "="*50 + "\n"
        output += f"Total Documents: {len(MOCK_DOCS)}\n\n"
        
        output += "CATEGORIES:\n"
        for category in sorted(by_category.keys()):
            docs = by_category[category]
            output += f"\n📁 {category.upper()} ({len(docs)} document{'s' if len(docs) != 1 else ''})\n"
            
            for doc in docs:
                output += f"   • {doc['title']}\n"
                output += f"     Tags: {', '.join(doc['tags'][:3])}{'...' if len(doc['tags']) > 3 else ''}\n"
        
        print(f"[TOOL LOG] Listed all {len(MOCK_DOCS)} documents")
        return output
        
    except Exception as e:
        error_msg = f"❌ Error listing documents: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


# =============================================================================
# EXPORT TOOLS
# =============================================================================

doc_tools = [
    retrieve_documents,
    search_by_category,
    list_all_documents,
]
"""
Lista de herramientas de documentos disponibles.

Uso en src/tools/__init__.py:
    from src.tools.docs import doc_tools
    all_tools = finance_tools + health_tools + doc_tools
"""


# =============================================================================
# DEBUG / TESTING (Opcional - para probar en terminal)
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING DOCUMENT RETRIEVAL TOOLS")
    print("="*70 + "\n")
    
    # Test 1: Listar todos los documentos
    print("1️⃣ List all documents:")
    print(list_all_documents.invoke({}))
    print()
    
    # Test 2: Búsqueda por palabra clave
    print("2️⃣ Search for 'insurance':")
    result = retrieve_documents.invoke({"query": "insurance"})
    print(result)
    print()
    
    # Test 3: Búsqueda por múltiples palabras
    print("3️⃣ Search for 'rent payment':")
    result = retrieve_documents.invoke({"query": "rent payment"})
    print(result)
    print()
    
    # Test 4: Búsqueda por categoría
    print("4️⃣ Search by category 'health':")
    result = search_by_category.invoke({"category": "health"})
    print(result)
    print()
    
    # Test 5: Búsqueda sin resultados
    print("5️⃣ Search for 'xyz' (should not find):")
    result = retrieve_documents.invoke({"query": "xyz"})
    print(result)
    print()
    
    # Test 6: Búsqueda por nutrición
    print("6️⃣ Search for 'nutrition plan':")
    result = retrieve_documents.invoke({"query": "nutrition plan"})
    print(result)
    print()
    
    print("="*70)
    print("✅ All document tools tested successfully!")
    print("="*70)
