#!/bin/bash
# Quick Setup Script for Family AI Assistant
# ===========================================
# 
# Uso:
#   bash setup.sh
#
# Esto instala todo lo necesario para empezar

set -e  # Exit on error

echo "🚀 Setting up Family AI Assistant..."
echo ""

# ========== Check Python ==========
echo "✓ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi
python_version=$(python3 --version | cut -d' ' -f2)
echo "  Found Python $python_version"
echo ""

# ========== Create Virtual Environment ==========
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Created venv/"
else
    echo "  venv/ already exists"
fi
echo ""

# ========== Activate Virtual Environment ==========
echo "✓ Activating virtual environment..."
source venv/bin/activate
echo "  Virtual environment activated"
echo ""

# ========== Upgrade pip ==========
echo "✓ Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "  pip upgraded"
echo ""

# ========== Install Dependencies ==========
echo "✓ Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
echo "  All dependencies installed:"
echo "    - streamlit"
echo "    - langchain"
echo "    - langgraph"
echo "    - pydantic"
echo "    - openai"
echo ""

# ========== Create Streamlit Secrets ==========
echo "✓ Setting up Streamlit secrets..."
mkdir -p ~/.streamlit

if [ ! -f ~/.streamlit/secrets.toml ]; then
    cat > ~/.streamlit/secrets.toml << EOF
# Streamlit Secrets - Add your API keys here
OPENAI_API_KEY = "sk-proj-your-key-here"
EOF
    chmod 600 ~/.streamlit/secrets.toml
    echo "  Created ~/.streamlit/secrets.toml"
    echo "  ⚠️  IMPORTANT: Edit ~/.streamlit/secrets.toml and add your real OpenAI API key"
else
    echo "  ~/.streamlit/secrets.toml already exists"
fi
echo ""

# ========== Validate Structure ==========
echo "✓ Validating project structure..."
if python validate_structure.py > /dev/null 2>&1; then
    echo "  ✓ Project structure is valid"
else
    echo "  ⚠️  Some warnings in structure check (this is OK if dependencies aren't installed yet)"
fi
echo ""

# ========== Show Instructions ==========
echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit your API key:"
echo "   nano ~/.streamlit/secrets.toml"
echo ""
echo "2. Run the app:"
echo "   streamlit run app.py"
echo ""
echo "3. Open browser to:"
echo "   http://localhost:8501"
echo ""
echo "Happy coding! 🚀"
