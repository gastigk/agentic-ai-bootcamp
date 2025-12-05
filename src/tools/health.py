"""
Health & Habits Tools for Family AI Assistant
==============================================

Herramientas personalizadas (@tool decorators) para el tracking de hábitos
y objetivos de salud.

Patrón Replicado: 2_Chatbot_Agent.py (líneas 20-35)
- Uso de @tool decorator de langchain_core.tools
- Docstrings detallados para que el router sepa cuándo usarlas
- Type hints para validación
- Encapsulación de lógica (MOCK_DB simula PostgreSQL)

Hábitos soportados: gym, reading, meditation, sleep, water, coding
"""

# =============================================================================
# IMPORTS
# =============================================================================

from langchain_core.tools import tool
from typing import Optional, List
from datetime import datetime, timedelta


# =============================================================================
# MOCK DATABASE (Simula PostgreSQL)
# =============================================================================

MOCK_DB = {
    "user_123": {
        "habits": {
            # Estructura: habit_name -> {"target": freq, "check_ins": [dates]}
            "gym": {
                "target": 3,  # 3 veces por semana
                "unit": "times_per_week",
                "check_ins": [
                    "2025-12-01",
                    "2025-12-03",
                    "2025-12-04",
                ],
            },
            "reading": {
                "target": 4,  # 4 libros por mes
                "unit": "books_per_month",
                "check_ins": [
                    {"date": "2025-12-01", "book": "Atomic Habits"},
                    {"date": "2025-12-15", "book": "Thinking, Fast and Slow"},
                ],
            },
            "meditation": {
                "target": 5,  # 5 días por semana
                "unit": "times_per_week",
                "check_ins": [
                    "2025-12-01",
                    "2025-12-02",
                    "2025-12-03",
                ],
            },
            "sleep": {
                "target": 8,  # 8 horas mínimo
                "unit": "hours_per_day",
                "check_ins": [
                    {"date": "2025-12-01", "hours": 7.5},
                    {"date": "2025-12-02", "hours": 8.0},
                    {"date": "2025-12-03", "hours": 7.0},
                ],
            },
        },
        "milestones": {
            "gym": {"streak_current": 2, "streak_best": 7},
            "reading": {"books_completed": 2},
            "meditation": {"days_active": 45},
        },
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_user_db(user_id: str) -> dict:
    """Obtiene la DB del usuario, o crea una nueva."""
    if user_id not in MOCK_DB:
        MOCK_DB[user_id] = {
            "habits": {},
            "milestones": {},
        }
    return MOCK_DB[user_id]


def _get_week_start() -> str:
    """Devuelve la fecha del lunes de esta semana."""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%d")


def _count_week_check_ins(check_ins: list) -> int:
    """Cuenta check-ins en la semana actual."""
    week_start = datetime.strptime(_get_week_start(), "%Y-%m-%d")
    count = 0
    for check_in in check_ins:
        if isinstance(check_in, str):
            check_date = datetime.strptime(check_in, "%Y-%m-%d")
        else:
            check_date = datetime.strptime(check_in.get("date", ""), "%Y-%m-%d")
        
        if check_date >= week_start:
            count += 1
    return count


# =============================================================================
# TOOLS (Decoradas con @tool - Patrón Bootcamp 2)
# =============================================================================

@tool
def log_habit(
    user_id: str,
    habit_name: str,
    additional_info: str = "",
) -> str:
    """
    Log a completed habit or health activity.
    
    This tool records that the user has completed a specific habit today.
    Use this when the user reports doing an activity like:
    - "I went to the gym"
    - "I read a book"
    - "I meditated for 20 minutes"
    - "I got 8 hours of sleep"
    
    Args:
        user_id: The user's unique identifier
        habit_name: Name of the habit. Valid values:
                    'gym', 'reading', 'meditation', 'sleep', 'water', 'coding'
        additional_info: Optional details (e.g., "30 minutes", "Finished one book", "8.5 hours")
    
    Returns:
        Confirmation message with streak and progress update
    
    Example:
        >>> log_habit("user_123", "gym", "45 minutes weight training")
        "✅ Gym logged! Current streak: 3 days\n Progress: 3/3 this week"
    """
    try:
        print(f"[TOOL LOG] log_habit called: habit={habit_name}, info={additional_info}")
        
        user_db = _get_user_db(user_id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        valid_habits = ["gym", "reading", "meditation", "sleep", "water", "coding"]
        if habit_name not in valid_habits:
            return f"❌ Invalid habit '{habit_name}'. Valid: {', '.join(valid_habits)}"
        
        # Crear hábito si no existe
        if habit_name not in user_db["habits"]:
            user_db["habits"][habit_name] = {
                "target": 3,
                "unit": "times_per_week",
                "check_ins": [],
            }
        
        habit = user_db["habits"][habit_name]
        
        # Evitar duplicados el mismo día
        if today in [str(c) if isinstance(c, str) else c.get("date", "") for c in habit["check_ins"]]:
            return f"⚠️ You've already logged {habit_name} today! One entry per day."
        
        # Registrar check-in
        check_in = {
            "date": today,
            "info": additional_info,
        } if additional_info else today
        
        habit["check_ins"].append(check_in)
        
        # Calcular racha
        week_count = _count_week_check_ins(habit["check_ins"])
        target = habit.get("target", 3)
        
        # Actualizar milestones
        if habit_name not in user_db["milestones"]:
            user_db["milestones"][habit_name] = {"streak_current": 1, "streak_best": 1}
        
        milestone = user_db["milestones"][habit_name]
        milestone["streak_current"] = week_count
        milestone["streak_best"] = max(milestone.get("streak_best", 0), week_count)
        
        # Generar mensaje
        progress_emoji = "🔥" if week_count >= target else "💪"
        
        if week_count >= target:
            status = f"🎉 TARGET REACHED! {week_count}/{target} this week!"
        else:
            status = f"{week_count}/{target} completed this week"
        
        print(f"[TOOL LOG] Habit logged. Week progress: {week_count}/{target}")
        
        return (
            f"✅ {habit_name.upper()} logged!\n"
            f"{progress_emoji} {status}\n"
            f"📊 Details: {additional_info or 'Completed'}"
        )
        
    except Exception as e:
        error_msg = f"❌ Error logging habit: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def check_habit_progress(
    user_id: str,
    habit_name: Optional[str] = None,
) -> str:
    """
    Check progress on a specific habit or all habits.
    
    This tool shows how well the user is tracking with their habits.
    Displays weekly progress, streaks, and motivation.
    
    Use this when the user asks:
    - "How am I doing with my gym routine?"
    - "What's my meditation progress?"
    - "Show my habit tracking"
    - "Am I on track with my goals?"
    
    Args:
        user_id: The user's unique identifier
        habit_name: Optional - check only this habit. If None, show all habits.
    
    Returns:
        Formatted progress report with weekly stats and streaks
    
    Example:
        >>> check_habit_progress("user_123", "gym")
        "🏋️ GYM PROGRESS\n
         This Week: 3/3 ✅\n
         Current Streak: 3 days\n
         Best Streak: 7 days"
    """
    try:
        print(f"[TOOL LOG] check_habit_progress called: habit={habit_name}")
        
        user_db = _get_user_db(user_id)
        
        if not user_db["habits"]:
            return "📭 No habits tracked yet. Start by logging a habit!"
        
        # Si se especifica un hábito
        if habit_name:
            valid_habits = ["gym", "reading", "meditation", "sleep", "water", "coding"]
            if habit_name not in valid_habits:
                return f"❌ Invalid habit '{habit_name}'"
            
            if habit_name not in user_db["habits"]:
                return f"ℹ️ {habit_name} not tracked yet. Start logging to see progress!"
            
            habit = user_db["habits"][habit_name]
            target = habit.get("target", 3)
            check_ins = habit.get("check_ins", [])
            week_count = _count_week_check_ins(check_ins)
            
            milestone = user_db["milestones"].get(habit_name, {})
            streak = milestone.get("streak_current", 0)
            best_streak = milestone.get("streak_best", 0)
            
            # Evaluar desempeño
            if week_count >= target:
                eval_icon = "🌟"
                eval_text = "EXCELLENT!"
            elif week_count >= target * 0.7:
                eval_icon = "😊"
                eval_text = "Good progress!"
            elif week_count > 0:
                eval_icon = "💪"
                eval_text = "Keep going!"
            else:
                eval_icon = "🚀"
                eval_text = "Time to start!"
            
            print(f"[TOOL LOG] Progress retrieved: {week_count}/{target}")
            
            return (
                f"📊 {habit_name.upper()} PROGRESS\n"
                f"{'='*40}\n"
                f"This Week: {week_count}/{target} {eval_icon}\n"
                f"Status: {eval_text}\n"
                f"Current Streak: {streak} days\n"
                f"Best Streak: {best_streak} days\n"
                f"Total Logged: {len(check_ins)} times"
            )
        
        # Mostrar todos los hábitos
        else:
            report = "📊 ALL HABITS PROGRESS\n" + "="*40 + "\n"
            
            for habit_name, habit_data in user_db["habits"].items():
                target = habit_data.get("target", 3)
                check_ins = habit_data.get("check_ins", [])
                week_count = _count_week_check_ins(check_ins)
                
                milestone = user_db["milestones"].get(habit_name, {})
                streak = milestone.get("streak_current", 0)
                
                # Status emoji
                if week_count >= target:
                    status = "✅"
                elif week_count > 0:
                    status = "⚠️ "
                else:
                    status = "❌"
                
                report += f"\n{status} {habit_name.upper()}\n"
                report += f"   Progress: {week_count}/{target}\n"
                report += f"   Streak: {streak} days\n"
            
            print(f"[TOOL LOG] All habits progress retrieved")
            return report
        
    except Exception as e:
        error_msg = f"❌ Error checking progress: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def get_health_summary(user_id: str) -> str:
    """
    Get a comprehensive health and habits summary.
    
    This tool provides a complete overview of the user's health journey:
    - Overall habit compliance
    - Weekly streaks and trends
    - Milestones achieved
    - Motivational insights
    - Recommendations
    
    Use this when the user asks:
    - "How's my overall health?"
    - "Give me a health summary"
    - "What's my wellness score?"
    - "Am I meeting my health goals?"
    
    Args:
        user_id: The user's unique identifier
    
    Returns:
        Formatted health dashboard with metrics and recommendations
    
    Example:
        >>> get_health_summary("user_123")
        "💪 HEALTH DASHBOARD\n
         Habits Tracked: 4/6\n
         Weekly Compliance: 75%\n
         Active Streak: 5 days"
    """
    try:
        print(f"[TOOL LOG] get_health_summary called")
        
        user_db = _get_user_db(user_id)
        
        habits = user_db["habits"]
        if not habits:
            return (
                "💪 HEALTH DASHBOARD\n"
                "="*40 + "\n"
                "📭 No habits tracked yet!\n\n"
                "Start your wellness journey:\n"
                "• Log your first habit\n"
                "• Set realistic targets\n"
                "• Build consistency"
            )
        
        # Calcular métricas
        total_habits = len(habits)
        active_habits = sum(1 for h in habits.values() if h.get("check_ins"))
        
        # Compliance rate
        total_target = sum(h.get("target", 3) for h in habits.values())
        total_completed = sum(_count_week_check_ins(h.get("check_ins", [])) for h in habits.values())
        compliance = (total_completed / total_target * 100) if total_target > 0 else 0
        
        # Best habit
        best_habit = None
        best_score = 0
        for name, habit in habits.items():
            score = _count_week_check_ins(habit.get("check_ins", []))
            if score > best_score:
                best_score = score
                best_habit = name
        
        # Wellness score
        if compliance >= 90:
            wellness_icon = "🌟"
            wellness_text = "EXCELLENT"
        elif compliance >= 70:
            wellness_icon = "😊"
            wellness_text = "GOOD"
        elif compliance >= 50:
            wellness_icon = "💪"
            wellness_text = "FAIR"
        else:
            wellness_icon = "🚀"
            wellness_text = "STARTING"
        
        # Recomendaciones
        recommendations = []
        if compliance < 70:
            recommendations.append("📌 Try to reach 70% compliance this week")
        if active_habits < total_habits:
            recommendations.append(f"📌 Start tracking {total_habits - active_habits} more habit(s)")
        if best_habit:
            recommendations.append(f"📌 Keep up your {best_habit} streak!")
        
        rec_text = "\n".join([f"  {r}" for r in recommendations]) if recommendations else "✅ All good!"
        
        print(f"[TOOL LOG] Health summary generated. Compliance: {compliance:.1f}%")
        
        return (
            f"💪 HEALTH DASHBOARD\n"
            f"{'='*40}\n"
            f"Wellness Score: {wellness_icon} {wellness_text} ({compliance:.1f}%)\n\n"
            f"📊 STATS:\n"
            f"  • Habits Active: {active_habits}/{total_habits}\n"
            f"  • Weekly Target: {total_completed}/{total_target}\n"
            f"  • Best Habit: {best_habit}\n"
            f"  • Score: {best_score}/{habits[best_habit].get('target', 3)}\n\n"
            f"💡 RECOMMENDATIONS:\n"
            f"{rec_text}\n"
        )
        
    except Exception as e:
        error_msg = f"❌ Error generating health summary: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


@tool
def get_habit_motivation(user_id: str, habit_name: Optional[str] = None) -> str:
    """
    Get personalized motivation and encouragement.
    
    This tool generates motivational messages based on:
    - Current habit streaks
    - Progress towards goals
    - Historical performance
    - Time-based patterns
    
    Use this when the user needs motivation:
    - "Motivate me"
    - "I need encouragement"
    - "Should I skip today?"
    - "Why should I keep going?"
    
    Args:
        user_id: The user's unique identifier
        habit_name: Optional - get motivation for specific habit
    
    Returns:
        Personalized motivational message
    
    Example:
        >>> get_habit_motivation("user_123", "gym")
        "🔥 You're on a 3-day streak! Keep it up!\n
         Just 1 more day to beat your previous best of 7 days!"
    """
    try:
        print(f"[TOOL LOG] get_habit_motivation called: habit={habit_name}")
        
        user_db = _get_user_db(user_id)
        
        if habit_name:
            if habit_name not in user_db["habits"]:
                return f"ℹ️ No motivation data yet for {habit_name}. Start logging to build momentum!"
            
            habit = user_db["habits"][habit_name]
            milestone = user_db["milestones"].get(habit_name, {})
            
            current_streak = milestone.get("streak_current", 0)
            best_streak = milestone.get("streak_best", 0)
            target = habit.get("target", 3)
            
            # Mensajes motivacionales personalizados
            if current_streak >= target:
                msg = f"🔥 You crushed it! {current_streak}/{target} for {habit_name}!"
            elif current_streak > 0 and current_streak < target:
                remaining = target - current_streak
                msg = f"💪 {current_streak} done! Just {remaining} more for {habit_name}!"
            elif current_streak == 0 and best_streak > 0:
                msg = f"🚀 You've done {best_streak} before! Let's beat that again!"
            else:
                msg = f"✨ Today is the day to start {habit_name}!"
            
            # Comparación con mejor racha
            if best_streak > current_streak and best_streak > 0:
                msg += f"\n📈 Your best: {best_streak} days. Let's surpass it!"
            
            print(f"[TOOL LOG] Motivation generated for {habit_name}")
            return msg
        
        else:
            # Motivación general
            total_streak = sum(
                user_db["milestones"].get(name, {}).get("streak_current", 0)
                for name in user_db["habits"].keys()
            )
            
            if total_streak >= 10:
                return (
                    "🌟 You're on FIRE! Keep that momentum going!\n"
                    "Your consistency is inspiring. Keep it up! 🚀"
                )
            elif total_streak >= 5:
                return (
                    "💪 Great work! You're building strong habits!\n"
                    "Every day counts. You're doing amazing! 🎉"
                )
            elif total_streak > 0:
                return (
                    "✨ You've started your journey! Keep going!\n"
                    "Small steps lead to big changes. You got this! 💪"
                )
            else:
                return (
                    "🚀 Ready to build amazing habits?\n"
                    "Today is the perfect day to start!\n"
                    "One habit, one day at a time. Let's go! 🔥"
                )
        
    except Exception as e:
        error_msg = f"❌ Error generating motivation: {str(e)}"
        print(f"[TOOL LOG] {error_msg}")
        return error_msg


# =============================================================================
# EXPORT TOOLS
# =============================================================================

health_tools = [
    log_habit,
    check_habit_progress,
    get_health_summary,
    get_habit_motivation,
]
"""
Lista de herramientas de salud y hábitos disponibles.

Uso en src/graph.py:
    from src.tools.health import health_tools
    llm_with_tools = llm.bind_tools(health_tools)
"""


# =============================================================================
# DEBUG / TESTING
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTING HEALTH & HABITS TOOLS")
    print("="*70 + "\n")
    
    user_id = "user_123"
    
    # Test 1: Get initial health summary
    print("1️⃣ Initial Health Summary:")
    print(get_health_summary.invoke({"user_id": user_id}))
    print()
    
    # Test 2: Log a habit
    print("2️⃣ Log gym workout:")
    result = log_habit.invoke({
        "user_id": user_id,
        "habit_name": "gym",
        "additional_info": "45 minutes strength training",
    })
    print(result)
    print()
    
    # Test 3: Check habit progress
    print("3️⃣ Check gym progress:")
    print(check_habit_progress.invoke({
        "user_id": user_id,
        "habit_name": "gym",
    }))
    print()
    
    # Test 4: Get motivation
    print("4️⃣ Get motivation:")
    print(get_habit_motivation.invoke({
        "user_id": user_id,
        "habit_name": "gym",
    }))
    print()
    
    # Test 5: Check all habits
    print("5️⃣ All habits progress:")
    print(check_habit_progress.invoke({"user_id": user_id}))
    print()
    
    print("="*70)
    print("✅ All health tools tested successfully!")
    print("="*70)
