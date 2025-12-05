#!/usr/bin/env python3
"""
Validation Script for Family AI Assistant Project
===================================================

Verifica que la estructura del proyecto sea correcta antes de proceder.
Útil para CI/CD y validación local.

Uso:
    python validate_structure.py
"""

import os
import sys
from pathlib import Path

# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def check(condition: bool, message: str) -> bool:
    """Print check result with color."""
    symbol = f"{Colors.GREEN}✓{Colors.END}" if condition else f"{Colors.RED}✗{Colors.END}"
    status = f"{Colors.GREEN}OK{Colors.END}" if condition else f"{Colors.RED}FAIL{Colors.END}"
    print(f"{symbol} {message:<50} [{status}]")
    return condition


def main():
    """Run all validation checks."""
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}Family AI Assistant - Structure Validation{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")

    root = Path(".")
    all_passed = True

    # ========== Check Root Files ==========
    print(f"{Colors.YELLOW}📁 Root Files:{Colors.END}")
    
    required_root_files = [
        "app.py",
        "requirements.txt",
        "copilot-rules.md",
        "README.md",
        "TAREA_1_COMPLETADA.md",
        ".gitignore",  # Espera que exista o es OK que no
    ]
    
    for file in required_root_files:
        if file == ".gitignore":
            check(Path(file).exists(), f"  {file}")
        else:
            all_passed &= check(Path(file).exists(), f"  {file}")

    # ========== Check Directory Structure ==========
    print(f"\n{Colors.YELLOW}📂 Directory Structure:{Colors.END}")
    
    required_dirs = [
        "src",
        "src/agents",
        "src/tools",
        "src/database",
        "src/rag",
        ".streamlit",
    ]
    
    for dir_path in required_dirs:
        all_passed &= check(Path(dir_path).is_dir(), f"  {dir_path}/")

    # ========== Check Python Modules ==========
    print(f"\n{Colors.YELLOW}🐍 Python Modules:{Colors.END}")
    
    required_modules = [
        "src/__init__.py",
        "src/state.py",
        "src/agents/__init__.py",
        "src/tools/__init__.py",
        "src/database/__init__.py",
        "src/rag/__init__.py",
    ]
    
    for module in required_modules:
        all_passed &= check(Path(module).exists(), f"  {module}")

    # ========== Check Configuration Files ==========
    print(f"\n{Colors.YELLOW}⚙️ Configuration Files:{Colors.END}")
    
    config_files = {
        ".streamlit/secrets.toml": "secrets (for API keys)",
    }
    
    for file, description in config_files.items():
        exists = Path(file).exists()
        check(exists, f"  {file:<30} ({description})")

    # ========== Validate Python Syntax ==========
    print(f"\n{Colors.YELLOW}✓ Python Syntax Check:{Colors.END}")
    
    import py_compile
    python_files = [
        "app.py",
        "src/state.py",
    ]
    
    for py_file in python_files:
        try:
            py_compile.compile(py_file, doraise=True)
            check(True, f"  {py_file:<30} (syntax)")
        except py_compile.PyCompileError as e:
            check(False, f"  {py_file:<30} (syntax)")
            print(f"    {Colors.RED}Error: {e}{Colors.END}")
            all_passed = False

    # ========== Check Imports in src/state.py ==========
    print(f"\n{Colors.YELLOW}📦 Import Check (src/state.py):{Colors.END}")
    
    try:
        from src.state import AgentState, Goal, UserContext, create_initial_state
        check(True, "  AgentState (TypedDict)")
        check(True, "  Goal (Pydantic model)")
        check(True, "  UserContext (Pydantic model)")
        check(True, "  create_initial_state (factory function)")
    except ImportError as e:
        check(False, f"  Import error: {e}")
        all_passed = False

    # ========== Check Imports in app.py ==========
    print(f"\n{Colors.YELLOW}📦 Import Check (app.py):{Colors.END}")
    
    try:
        # No ejecutar todo app.py porque requiere Streamlit,
        # solo hacer checks básicos
        with open("app.py", "r") as f:
            content = f.read()
            
        checks = {
            "import streamlit as st": "Streamlit import",
            "from src.state import": "src.state import",
            "st.set_page_config": "Streamlit config",
            "st.chat_input": "Chat input component",
            "st.chat_message": "Chat message component",
        }
        
        for code_snippet, description in checks.items():
            check(code_snippet in content, f"  {description}")
            
    except Exception as e:
        check(False, f"  Error checking app.py: {e}")
        all_passed = False

    # ========== Check requirements.txt ==========
    print(f"\n{Colors.YELLOW}📋 Dependencies (requirements.txt):{Colors.END}")
    
    try:
        with open("requirements.txt", "r") as f:
            deps = f.read().lower()
        
        required_deps = [
            ("streamlit", "Streamlit"),
            ("langchain", "LangChain"),
            ("langgraph", "LangGraph"),
            ("pydantic", "Pydantic"),
            ("openai", "OpenAI"),
        ]
        
        for dep, name in required_deps:
            check(dep in deps, f"  {name:<20} (in requirements.txt)")
            
    except Exception as e:
        check(False, f"  Error reading requirements.txt: {e}")
        all_passed = False

    # ========== Summary ==========
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    
    if all_passed:
        print(f"{Colors.GREEN}✓ All checks passed! Project structure is valid.{Colors.END}")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}✗ Some checks failed. Please fix the issues above.{Colors.END}")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
