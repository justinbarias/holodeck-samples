# Customer Support Agent - Azure OpenAI

A context-aware customer support chatbot with knowledge base integration, powered by Azure OpenAI.

## Overview

This sample demonstrates:
- **RAG (Retrieval-Augmented Generation)**: Knowledge base and FAQ lookup via ChromaDB
- **Conversation Memory**: MCP-based memory server for context persistence
- **RAG Evaluations**: Faithfulness, answer relevancy, contextual relevancy metrics
- **Quality Evaluations**: G-Eval for helpfulness and professionalism
- **Full-featured Frontend**: CopilotKit with multimodal file support

## Prerequisites

1. **Azure OpenAI Resource** with:
   - `gpt-4o` deployment
   - `text-embedding-ada-002` deployment

2. **Infrastructure** (from `/samples` root):
   ```bash
   ./start-infra.sh
   ```

3. **Node.js 18+** for CopilotKit frontend

## Setup

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure OpenAI credentials
   ```

2. **Initialize vector stores** (first run):
   ```bash
   holodeck init-vectors agent.yaml
   ```

3. **Start the agent**:
   ```bash
   holodeck serve agent.yaml --port 8001
   ```

4. **Start the frontend**:
   ```bash
   cd copilotkit
   npm install
   npm run dev
   ```

5. **Open the UI**: http://localhost:3000

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `knowledge_base` | VectorStore | Product documentation and support articles |
| `faq` | VectorStore | Frequently asked questions database |
| `memory` | MCP | Conversation context persistence |
| `escalate_to_human` | Prompt | Generate escalation summaries |

## Evaluations

| Metric | Type | Threshold | Purpose |
|--------|------|-----------|---------|
| Faithfulness | RAG | 0.8 | Grounded in retrieved knowledge |
| Answer Relevancy | RAG | 0.75 | Directly addresses questions |
| Contextual Relevancy | RAG | 0.7 | Retrieved context is relevant |
| Helpfulness | G-Eval | 0.8 | Provides actionable solutions |
| Professionalism | G-Eval | 0.7 | Appropriate tone and language |

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

## Data Files

- `data/knowledge_base.md` - Product documentation (2000+ words)
- `data/faq.json` - Frequently asked questions
- `data/product_catalog.json` - Product features and pricing

## Customization

1. **Add knowledge**: Update `data/knowledge_base.md` with your documentation
2. **Add FAQs**: Extend `data/faq.json` with common questions
3. **Modify persona**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`
