# Family AI Assistant - DataScienceDojo Agentic AI Bootcamp

A multi-agent AI assistant using LangChain, LangGraph, and RAG for personalized finance, health, and document analysis.

## Project Overview

Family AI Assistant is a multi-agent AI system built as the capstone project for the DataScienceDojo Agentic AI Bootcamp. It demonstrates advanced implementation of agentic AI patterns, tool calling, state management, and conditional routing.

### The Problem It Solves

Families often require personalized assistance across multiple disparate domains. This application consolidates these needs into a single interface:

- **Financial Planning**: Budget tracking, investment advice, and spending analysis.
- **Health Management**: Medical information retrieval, symptom analysis, and wellness tips.
- **Document Processing**: Centralized file access, content summarization, and data extraction.

The assistant provides a unified interface powered by specialized AI agents that route requests intelligently to provide domain-specific expertise.

## Key Capabilities

- **Smart Routing**: Automatically detects user intent via keyword analysis and context scoring to route requests to the appropriate specialist agent.
- **RAG Pipeline**: Retrieves and processes user documents using a Retrieve-Grade-Rewrite-Generate pattern for high accuracy.
- **Tool Calling**: Executes Python functions and processes results seamlessly within the agent workflow.
- **Graceful Fallbacks**: Handles errors robustly and provides helpful alternatives when specific tools fail.
- **Multi-Agent Coordination**: Orchestrates multiple specialized AI agents working in tandem.
- **Google Drive Integration**: Includes optional Model Context Protocol (MCP) support for external file access.

## Architecture

The system utilizes a hub-and-spoke architecture managed by a central router.

```
graph LR
    A["User Query"] --> B["Streamlit Interface"]
    B --> C["LangGraph Router"]
    C -->|"Finance Keywords"| D["Finance Agent"]
    C -->|"Health Keywords"| E["Health Agent"]
    C -->|"Document Keywords"| F["RAG Agent"]
    C -->|"Drive Keywords"| G["Drive Agent (MCP)"]
    C -->|"Other"| H["General Agent"]
    D --> I["Tool Execution"]
    E --> I
    F --> I
    G --> I
    H --> I
    I --> J["Response to User"]
    J --> B
    
    style A fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style B fill:#7B68EE,stroke:#5A4A9A,color:#fff
    style C fill:#FF6B6B,stroke:#D63031,color:#fff
    style D fill:#FFD93D,stroke:#C9A800,color:#000
    style E fill:#6BCB77,stroke:#4A9D5F,color:#fff
    style F fill:#4D96FF,stroke:#3570C9,color:#fff
    style G fill:#A0522D,stroke:#6D3A1F,color:#fff
    style H fill:#95A5A6,stroke:#7F8C8D,color:#fff
```

## Technologies and Concepts Implemented

This project showcases the practical application of the following technologies and patterns:

### Core Frameworks

- **LangChain 0.1+**: Used for constructing the base logic of AI applications.
- **LangGraph**: Used for orchestrating multi-agent workflows and cyclic graphs.
- **Streamlit**: Used for the interactive web-based frontend.
- **Pydantic**: Used for strict data validation and type safety within the state.

### Agentic AI Patterns

- **StateGraph**: Definition of agent workflow states and transitions.
- **Tool Calling**: Implementation of the @tool decorator for function definitions.
- **Conditional Edges**: Dynamic routing logic based on conversation context.
- **Message Passing**: Structured communication flow between nodes.
- **Error Handling**: Implementation of graceful degradation and fallback mechanisms.
- **ReAct Pattern**: Implementation of Reasoning and Acting loops.

### Advanced Features

- **RAG Pipeline**: Implementation of a Retrieve → Grade → Rewrite → Generate workflow.
- **Agent Specialization**: Use of domain-specific system prompts.
- **Async Operations**: Non-blocking I/O for improved performance.
- **Model Context Protocol (MCP)**: Integration with external services (Google Drive).

## Project Structure

```
family-ai-assistant/

├── src/                           # Core application source code
│   ├── __init__.py
│   ├── state.py                   # Pydantic TypedDict for state management
│   ├── llm.py                     # LLM initialization and configuration
│   ├── graph.py                   # Main StateGraph orchestration
│   ├── tools/                     # Specialized tools and agents
│   │   ├── __init__.py
│   │   ├── finance_tools.py       # Financial analysis tools
│   │   ├── health_tools.py        # Health & wellness tools
│   │   ├── doc_tools.py           # Document processing
│   │   ├── rag.py                 # RAG pipeline implementation
│   │   └── drive_mcp.py           # Google Drive MCP integration
│   │
│   └── agents/                    # Sub-graphs and specialized workflows
│       ├── __init__.py
│       └── rag_agentic.py         # Agentic RAG sub-graph
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_mcp_integration.py    # MCP functionality tests
│   ├── test_rag_integration.py    # RAG pipeline tests
│   └── validate_structure.py      # Project structure validation
│
├── app.py                         # Main Streamlit application entry point
├── Home.py                        # Streamlit home page
│
├── 1_Basic_Chatbot.py             # Tutorial: Simple chatbot
├── 2_Chatbot_Agent.py             # Tutorial: Agent with tool calling
├── 3_Chat_with_your_Data.py       # Tutorial: RAG pipeline
├── 4_MCP_Agent.py                 # Tutorial: MCP integration
│
├── requirements.txt               # Python dependencies
├── setup.sh                       # Setup and installation script
├── pytest.ini                     # Pytest configuration
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
│
├── MCP_INTEGRATION_GUIDE.md       # MCP implementation guide
├── RELEASE_CANDIDATE.md           # Release candidate checklist
└── README.md                      # This file
```

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager
- OpenAI API key

### Quick Start

1. Clone the repository:

```bash
git clone https://github.com/gastigk/agentic-ai-bootcamp.git
cd agentic-ai-bootcamp
```

2. Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

This script will create a virtual environment, install dependencies, and set up necessary directories.

3. Configure the environment:

```bash
cp .env.example .env
```

Edit the .env file and add your OPENAI_API_KEY.

4. Run the application:

```bash
streamlit run app.py
```

The application will launch at http://localhost:8501.

### Manual Setup

If you prefer to configure the environment manually:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"
streamlit run app.py
```

## Usage Scenarios

### 1. Financial Query

User: "How much did I spend on groceries last month?"

System Flow:
- Router detects "spend" keyword → Assigns Finance context.
- Routes to Finance Agent.
- Finance Agent analyzes spending patterns via tools.
- Response: "Based on your transactions, you spent $450 on groceries."

### 2. Health Query

User: "I have a fever and sore throat, what should I do?"

System Flow:
- Router detects "fever" and "sore throat" → Assigns Health context.
- Routes to Health Agent.
- Health Agent retrieves medical guidelines.
- Response: "These symptoms suggest a possible infection. Consult a doctor..."

### 3. Document Query (RAG)

User: "What was mentioned about investment options in my documents?"

System Flow:
- Router detects "documents" and "investment" → Assigns Document context.
- Routes to RAG Agent.
- RAG Pipeline execution:
  - Retrieve: Fetch relevant document chunks.
  - Grade: Score relevance of retrieved sections.
  - Rewrite: Improve query specificity if scores are low.
  - Generate: Create synthesis response.
- Response: "Your documents mention 401k, IRA, and stock options..."

## Learning Objectives

This project demonstrates proficiency in the following areas:

- **Fundamentals**: LLM basics, prompt engineering, and context management.
- **Intermediate Implementation**: Multi-agent systems, conditional routing, and error handling.
- **Advanced Architecture**: Sub-graphs, workflow composition, async operations, and MCP integration.

## Testing

### Running Tests via Pytest

To run the full test suite:

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

### Running Specific Modules

```bash
# Test MCP integration
python -m pytest tests/test_mcp_integration.py

# Test RAG pipeline
python -m pytest tests/test_rag_integration.py

# Validate project structure
python -m pytest tests/validate_structure.py
```

## Advanced Features

### Agentic RAG Sub-Graph

The RAG Agent employs a specialized sub-graph for intelligent document processing: RETRIEVE → GRADE → REWRITE → GENERATE

- **Retrieve**: Fetches the most relevant document chunks.
- **Grade**: Scores retrieved chunks for relevance using LLM evaluation.
- **Rewrite**: Reformulates the query if initial results are of low quality.
- **Generate**: Creates the final response based on the highest-quality chunks.

### Google Drive Integration (MCP)

The optional Model Context Protocol integration enables dynamic tool loading from external servers and secure file access without hardcoding credentials. See MCP_INTEGRATION_GUIDE.md for setup details.

## Configuration

### Environment Variables

- **OPENAI_API_KEY**: Required for LLM operations.
- **MCP_SERVER_URL**: Optional; required for Google Drive integration.
- **STREAMLIT_SERVER_PORT**: Customizes the server port (default: 8501).
- **LOG_LEVEL**: Sets logging verbosity (DEBUG, INFO, WARNING).

## Project Metrics

- **Agents**: 5 specialized agents (Finance, Health, Documents, Drive, General).
- **Tools**: Over 10 specialized functions across all domains.
- **Routing**: 30+ keywords configured for intelligent context detection.
- **Codebase**: 2,000+ lines of production code.

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"

Ensure the environment variable is set or the .env file is correctly configured.

### Issue: Streamlit connection refused

Check if port 8501 is in use. Run with a specific port: `streamlit run app.py --server.port 8502`.

### Issue: RAG not finding documents

Verify documents are located in the data/ directory and are in a supported format (PDF, TXT).

## License

This is an educational project for the DataScienceDojo Agentic AI Bootcamp. It is intended for learning purposes.
