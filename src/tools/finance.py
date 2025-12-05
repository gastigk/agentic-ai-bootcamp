"""
Finance Tools for Family AI Assistant
======================================

Herramientas personalizadas (@tool decorators) que el agente de Finanzas usará
para interactuar con gastos, presupuestos y transacciones.

Patrón Replicado: 2_Chatbot_Agent.py (líneas 20-35)
- Uso de @tool decorator de langchain_core.tools
- Docstrings detallados (crítico para que el router sepa cuándo usarlas)
- Type hints para validación
- Encapsulación de lógica (MOCK_DB simula PostgreSQL)

Nota: Este módulo simula DB con diccionarios.
En Tarea 3, reemplazaremos con queries a PostgreSQL reales.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from langchain_core.tools import tool
from typing import Optional
from datetime import datetime
from decimal import Decimal


# =============================================================================
# MOCK DATABASE (Simula PostgreSQL)
# =============================================================================

# ⚠️ Este diccionario simula la base de datos en memoria.
# En Tarea 3, lo reemplazaremos con:
#   from src.database.crud import insert_expense, get_balance, etc.

MOCK_DB = {
    # Usuarios con sus respectivas finanzas
    "user_123": {
        "expenses": [
            {
                "id": 1,
                "amount": 50.00,
                "category": "food",
                "description": "Groceries",
                "date": "2025-12-01",
            },
            {
                "id": 2,
                "amount": 30.00,
                "category": "transport",
                "description": "Uber",
                "date": "2025-12-02",
            },
            {
                "id": 3,
                "amount": 20.00,
                "category": "entertainment",
                "description": "Movie",
                "date": "2025-12-03",
            },
        ],
        "budgets": {
            "food": 200.00,
            "transport": 100.00,
            "entertainment": 50.00,
            "savings": 500.00,
        },
        "monthly_goals": {
            "savings": {"target": 500.00, "current": 150.00},
        },
    },
    # Otros usuarios pueden agregarse aquí
}


# =============================================================================
# HELPER FUNCTIONS (Interno - no son tools)
# =============================================================================

def _get_user_db(user_id: str) -> dict:
    """
    Obtiene la base de datos del usuario, o crea una nueva si no existe.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Diccionario con datos del usuario
    """
    if user_id not in MOCK_DB:
        MOCK_DB[user_id] = {
            "expenses": [],
            "budgets": {
                "food": 200.00,
                "transport": 100.00,
                "entertainment": 50.00,
                "savings": 500.00,
            },
            "monthly_goals": {},
        }
    return MOCK_DB[user_id]


def _get_category_spent(user_id: str, category: str) -> float:
    """
    Calcula cuánto se ha gastado en una categoría.
    
    Args:
        user_id: ID del usuario
        category: Categoría (ej: "food", "transport")
        
    Returns:
        Total gastado en esa categoría
    """
    user_db = _get_user_db(user_id)
    total = sum(
        exp["amount"]
        for exp in user_db["expenses"]
        if exp["category"] == category
    )
    return total


def _get_total_spent(user_id: str) -> float:
    """Total gastado en el mes."""
    user_db = _get_user_db(user_id)
    return sum(exp["amount"] for exp in user_db["expenses"])


# =============================================================================
# TOOLS (Decoradas con @tool - Patrón Bootcamp 2)
# =============================================================================

@tool
def add_expense(
    user_id: str,
    amount: float,
    category: str,
    description: str,
) -> str:
    """
    Add a new expense to the user's financial record.
    
    This tool logs a financial transaction (gasto) in the system.
    Use this when the user wants to record that they spent money.
    
    Args:
        user_id: The user's unique identifier
        amount: Amount spent (in USD or local currency)
        category: Category of expense. Valid values: 
                  'food', 'transport', 'entertainment', 'utilities', 'other'
        description: Brief description of what was bought
    
    Returns:
        Confirmation message with the recorded expense
    
    Example:
        >>> add_expense("user_123", 25.50, "food", "Lunch at restaurant")
        "✅ Expense recorded: $25.50 for 'Lunch at restaurant' (food category)"
    """
    try:
        print(f"[TOOL LOG] add_expense called: amount={amount}, category={category}")
        
        user_db = _get_user_db(user_id)
        
        # Validación
        if amount <= 0:
            return f"❌ Error: Amount must be positive. Got: {amount}"
        
        valid_categories = ["food", "transport", "entertainment", "utilities", "other"]
        if category not in valid_categories:
            return f"❌ Error: Invalid category '{category}'. Valid: {', '.join(valid_categories)}"
        
        # Crear registro
        new_expense = {
            "id": len(user_db["expenses"]) + 1,
            "amount": float(amount),
            "category": category,
            "description": description,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        
        user_db["expenses"].append(new_expense)
        
        # Información de presupuesto
        category_budget = user_db["budgets"].get(category, 0)
        category_spent = _get_category_spent(user_id, category)
        remaining = category_budget - category_spent
        
        print(f"[TOOL LOG] Expense added successfully. Remaining budget: ${remaining:.2f}")
        
        return (
            f"✅ Expense recorded: ${amount:.2f} for '{description}' ({category})\n"
            f"   Budget remaining for {category}: ${remaining:.2f}/{category_budget:.2f}"
        )
        
    except Exception as e:
        error_msg = f"❌ Error adding expense: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def check_budget(user_id: str, category: str) -> str:
    """
    Check the remaining budget for a specific expense category.
    
    This tool helps the user understand if they can afford a purchase
    based on their monthly budget and spending so far.
    
    Use this when the user asks questions like:
    - "How much can I spend on food?"
    - "Do I have budget for entertainment?"
    - "What's my transport spending limit?"
    
    Args:
        user_id: The user's unique identifier
        category: Category to check. Valid values:
                  'food', 'transport', 'entertainment', 'utilities', 'other'
    
    Returns:
        String with budget details and recommendations
    
    Example:
        >>> check_budget("user_123", "food")
        "Food Budget: $150.00/$200.00 remaining\n✅ You're within budget"
    """
    try:
        print(f"[TOOL LOG] check_budget called: category={category}")
        
        user_db = _get_user_db(user_id)
        
        # Validación
        if category not in user_db["budgets"]:
            return f"❌ Category '{category}' not found. Available: {list(user_db['budgets'].keys())}"
        
        budget = user_db["budgets"][category]
        spent = _get_category_spent(user_id, category)
        remaining = budget - spent
        percentage = (spent / budget * 100) if budget > 0 else 0
        
        # Generar recomendación
        if remaining <= 0:
            status = "🚨 BUDGET EXCEEDED"
        elif remaining < budget * 0.1:  # Menos del 10%
            status = "⚠️  WARNING: Low budget remaining"
        else:
            status = "✅ Within budget"
        
        print(f"[TOOL LOG] Budget check: {category} - {status}")
        
        return (
            f"💰 {category.upper()} Budget Status:\n"
            f"   Budget: ${budget:.2f}\n"
            f"   Spent: ${spent:.2f} ({percentage:.1f}%)\n"
            f"   Remaining: ${remaining:.2f}\n"
            f"   {status}"
        )
        
    except Exception as e:
        error_msg = f"❌ Error checking budget: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def get_balance(user_id: str) -> str:
    """
    Get a comprehensive financial summary for the user.
    
    This tool provides an overview of:
    - Total spending this month
    - Budget status for each category
    - Progress towards savings goals
    - Financial health indicator
    
    Use this when the user asks:
    - "What's my balance?"
    - "How much have I spent?"
    - "Show me my financial summary"
    - "Where is my money going?"
    
    Args:
        user_id: The user's unique identifier
    
    Returns:
        Formatted string with complete financial overview
    
    Example:
        >>> get_balance("user_123")
        "💳 FINANCIAL SUMMARY (December 2025)\n
         Total Spent: $100.00\n
         Monthly Budget: $900.00\n
         Remaining: $800.00\n
         📊 By Category: ..."
    """
    try:
        print(f"[TOOL LOG] get_balance called for user {user_id}")
        
        user_db = _get_user_db(user_id)
        
        total_spent = _get_total_spent(user_id)
        total_budget = sum(user_db["budgets"].values())
        total_remaining = total_budget - total_spent
        
        # Información por categoría
        category_details = []
        for category, budget in user_db["budgets"].items():
            spent = _get_category_spent(user_id, category)
            remaining = budget - spent
            percentage = (spent / budget * 100) if budget > 0 else 0
            
            category_details.append(
                f"  • {category.upper():<15} ${spent:>7.2f}/${budget:<7.2f} ({percentage:>5.1f}%)"
            )
        
        # Determinar salud financiera
        if total_remaining < 0:
            health = "🚨 CRITICAL - Over budget!"
        elif total_remaining < total_budget * 0.1:
            health = "⚠️  WARNING - Budget tight"
        elif total_remaining > total_budget * 0.5:
            health = "✅ HEALTHY - Good spending habits"
        else:
            health = "✅ OK - On track"
        
        # Goals progress
        goals_summary = ""
        if user_db["monthly_goals"]:
            goals_summary = "\n📈 Monthly Goals:\n"
            for goal_name, goal_data in user_db["monthly_goals"].items():
                current = goal_data.get("current", 0)
                target = goal_data.get("target", 0)
                progress = (current / target * 100) if target > 0 else 0
                goals_summary += f"  • {goal_name}: ${current:.2f}/${target:.2f} ({progress:.1f}%)\n"
        
        print(f"[TOOL LOG] Balance summary generated. Total: ${total_spent:.2f}")
        
        return (
            f"💳 FINANCIAL SUMMARY\n"
            f"{'='*45}\n"
            f"Total Spent: ${total_spent:.2f}\n"
            f"Monthly Budget: ${total_budget:.2f}\n"
            f"Remaining: ${total_remaining:.2f}\n"
            f"Health: {health}\n"
            f"\n📊 By Category:\n"
            + "\n".join(category_details)
            + goals_summary
        )
        
    except Exception as e:
        error_msg = f"❌ Error getting balance: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def get_spending_insights(user_id: str, category: Optional[str] = None) -> str:
    """
    Get AI-powered insights about spending patterns.
    
    This tool analyzes the user's spending and provides actionable recommendations:
    - Which categories are draining the most budget
    - Areas where they can save money
    - Progress towards goals
    - Trends in spending
    
    Use this when the user asks:
    - "Where should I save money?"
    - "Give me spending advice"
    - "What are my spending habits?"
    - "Where is most of my money going?"
    
    Args:
        user_id: The user's unique identifier
        category: Optional - analyze only this category
    
    Returns:
        String with personalized spending insights and recommendations
    
    Example:
        >>> get_spending_insights("user_123", "food")
        "🔍 Spending Insights\n
         Your food spending is HIGH (75% of budget)\n
         Recommendation: Consider meal planning..."
    """
    try:
        print(f"[TOOL LOG] get_spending_insights called: category={category}")
        
        user_db = _get_user_db(user_id)
        
        insights = "🔍 SPENDING INSIGHTS\n" + "="*45 + "\n"
        
        # Si se especifica categoría, analizar esa
        if category:
            if category not in user_db["budgets"]:
                return f"❌ Category '{category}' not found"
            
            spent = _get_category_spent(user_id, category)
            budget = user_db["budgets"][category]
            percentage = (spent / budget * 100) if budget > 0 else 0
            
            if percentage > 80:
                advice = f"⚠️  Your {category} spending is HIGH ({percentage:.1f}% of budget)"
                if category == "food":
                    advice += "\n💡 Consider: meal planning, cooking at home, bulk buying"
                elif category == "entertainment":
                    advice += "\n💡 Consider: free activities, streaming consolidation"
                elif category == "transport":
                    advice += "\n💡 Consider: public transport, carpooling, cycling"
            else:
                advice = f"✅ Your {category} spending is reasonable ({percentage:.1f}%)"
            
            insights += advice
            
        else:
            # Análisis general
            expenses = user_db["expenses"]
            if not expenses:
                insights += "No expenses recorded yet. Start tracking to get insights!"
                return insights
            
            # Categoría con mayor gasto
            category_totals = {}
            for exp in expenses:
                cat = exp["category"]
                category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
            
            if category_totals:
                max_category = max(category_totals, key=category_totals.get)
                max_amount = category_totals[max_category]
                total = sum(category_totals.values())
                percentage = (max_amount / total * 100) if total > 0 else 0
                
                insights += f"📌 Largest Expense Category: {max_category.upper()}\n"
                insights += f"   Amount: ${max_amount:.2f} ({percentage:.1f}% of total)\n\n"
                
                # Recomendación
                if percentage > 40:
                    insights += f"💡 Consider: {max_category} is taking up a large portion.\n"
                    insights += "   Try to balance spending across categories.\n"
                else:
                    insights += "✅ Good spending distribution across categories!\n"
            
            # Comparación con presupuesto
            total_spent = _get_total_spent(user_id)
            total_budget = sum(user_db["budgets"].values())
            budget_usage = (total_spent / total_budget * 100) if total_budget > 0 else 0
            
            insights += f"\n💰 Overall Budget Usage: {budget_usage:.1f}%\n"
            if budget_usage > 80:
                insights += "⚠️  You're approaching your monthly budget limit!"
            else:
                insights += "✅ You're on a good spending trajectory."
        
        print(f"[TOOL LOG] Insights generated successfully")
        return insights
        
    except Exception as e:
        error_msg = f"❌ Error generating insights: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


# =============================================================================
# EXPORT TOOLS
# =============================================================================

# Lista de herramientas de finanzas disponibles
# Se importará en src/graph.py para asignarse al LLM
finance_tools = [
    add_expense,
    check_budget,
    get_balance,
    get_spending_insights,
]
"""
Lista de herramientas de finanzas que el LLM puede usar.

Uso en src/graph.py:
    from src.tools.finance import finance_tools
    llm_with_tools = llm.bind_tools(finance_tools)
"""


# =============================================================================
# DEBUG / TESTING (Opcional - para probar en terminal)
# =============================================================================

if __name__ == "__main__":
    # Test de las herramientas
    print("\n" + "="*70)
    print("TESTING FINANCE TOOLS")
    print("="*70 + "\n")
    
    user_id = "user_123"
    
    # Test 1: Get initial balance
    print("1️⃣ Initial Balance:")
    print(get_balance.invoke({"user_id": user_id}))
    print()
    
    # Test 2: Add expense
    print("2️⃣ Add expense:")
    result = add_expense.invoke({
        "user_id": user_id,
        "amount": 45.50,
        "category": "food",
        "description": "Dinner with friends",
    })
    print(result)
    print()
    
    # Test 3: Check budget
    print("3️⃣ Check budget for food:")
    print(check_budget.invoke({"user_id": user_id, "category": "food"}))
    print()
    
    # Test 4: Get balance again
    print("4️⃣ Balance after expense:")
    print(get_balance.invoke({"user_id": user_id}))
    print()
    
    # Test 5: Spending insights
    print("5️⃣ Spending insights:")
    print(get_spending_insights.invoke({"user_id": user_id}))
    print()
    
    print("="*70)
    print("✅ All tools tested successfully!")
    print("="*70)
