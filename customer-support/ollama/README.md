# Customer Support Agent - Ollama

A context-aware customer support chatbot with knowledge base integration, powered by Ollama (local LLM).

## Overview

This sample demonstrates:
- **RAG (Retrieval-Augmented Generation)**: Knowledge base and FAQ lookup via ChromaDB
- **Conversation Memory**: MCP-based memory server for context persistence
- **RAG Evaluations**: Faithfulness, answer relevancy, contextual relevancy metrics
- **Quality Evaluations**: G-Eval for helpfulness and professionalism
- **Full-featured Frontend**: CopilotKit with multimodal file support
- **100% Local**: No cloud API keys required

## Prerequisites

1. **Ollama** installed and running:
   ```bash
   # Install Ollama (macOS)
   brew install ollama

   # Start Ollama service
   ollama serve
   ```

2. **Required models**:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text:latest
   ```

3. **Infrastructure** (from `/samples` root):
   ```bash
   ./start-infra.sh
   ```

4. **Node.js 18+** for CopilotKit frontend

## Setup

1. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit if using non-default Ollama endpoint
   ```

2. **Start the agent**:
   ```bash
   holodeck serve agent.yaml --port 8001
   ```

3. **Start the frontend**:
   ```bash
   cd copilotkit
   npm install
   npm run dev
   ```

4. **Open the UI**: http://localhost:3000

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `knowledge_base` | VectorStore | Product documentation and support articles |
| `faq` | VectorStore | Frequently asked questions database |
| `memory` | MCP | Conversation context persistence |
| `escalate_to_human` | Prompt | Generate escalation summaries |

## Evaluations

Note: Thresholds are slightly lower for local models compared to cloud providers.

| Metric | Type | Threshold | Purpose |
|--------|------|-----------|---------|
| Faithfulness | RAG | 0.75 | Grounded in retrieved knowledge |
| Answer Relevancy | RAG | 0.7 | Directly addresses questions |
| Contextual Relevancy | RAG | 0.65 | Retrieved context is relevant |
| Helpfulness | G-Eval | 0.75 | Provides actionable solutions |
| Professionalism | G-Eval | 0.65 | Appropriate tone and language |

## Testing

```bash
# Run all test cases
holodeck test agent.yaml --verbose

# Run specific tags
holodeck test agent.yaml --tags technical

# Output results to file
holodeck test agent.yaml --output results.md
```

## Observability

View traces and metrics in Aspire Dashboard: http://localhost:18888

## Hardware Requirements

- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **GPU**: Optional but improves performance significantly

## Data Files

- `data/knowledge_base.md` - Product documentation (2000+ words)
- `data/faq.json` - Frequently asked questions
- `data/product_catalog.json` - Product features and pricing

## Customization

1. **Add knowledge**: Update `data/knowledge_base.md` with your documentation
2. **Add FAQs**: Extend `data/faq.json` with common questions
3. **Modify persona**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`
5. **Change model**: Swap `llama3.1:8b` for other Ollama models
