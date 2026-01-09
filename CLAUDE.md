# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **holodeck-samples** repository - a collection of production-ready sample agents for the HoloDeck AI agent platform. HoloDeck enables building, testing, and deploying AI agents through pure YAML configuration without code.

## Common Commands

### Infrastructure
```bash
./start-infra.sh      # Start ChromaDB (localhost:8000) and Aspire Dashboard (localhost:18888)
./stop-infra.sh       # Stop infrastructure
```

### Agent Development
```bash
# Navigate to a sample first, e.g.: cd ticket-routing/openai

holodeck serve agent.yaml --port 8001   # Start agent API server
holodeck test agent.yaml --verbose      # Run test cases with evaluations
holodeck test agent.yaml --tags <tag>   # Run specific test cases by tag
holodeck chat agent.yaml                # Interactive chat session
```

### Frontend (CopilotKit)
```bash
cd <sample>/copilotkit
npm install
npm run dev    # Starts at http://localhost:3000
```

## Repository Structure

```
<use-case>/<provider>/
├── agent.yaml              # Main agent configuration
├── config.yaml             # Provider-specific settings
├── .env.example            # Environment variables template
├── instructions/
│   └── system-prompt.md    # Agent system prompt
├── data/
│   └── *.json, *.md        # Knowledge base and grounding data
└── copilotkit/             # Next.js frontend application
```

**Use cases:** ticket-routing, customer-support, content-moderation, legal-summarization

**Providers:** openai (gpt-4o), azure-openai (gpt-4o), ollama (llama3.1:8b local)

## Agent YAML Configuration

**IMPORTANT:** When writing or modifying any HoloDeck YAML files (`agent.yaml`, `config.yaml`), always reference the schema at `@schemas/agent.schema.json` for validation and autocomplete support. This schema defines all valid properties, types, and constraints.

The `agent.yaml` is the core configuration defining an agent:

- **model**: LLM provider, model name, temperature, max_tokens
- **response_format**: JSON schema for structured output (optional)
- **instructions**: System prompt (inline or file reference)
- **tools**: Vector stores (RAG), MCP servers, custom functions
- **evaluations**: Metrics configuration (GEval, RAG metrics, standard NLP metrics)
- **test_cases**: Input/output pairs with expected tools and ground truth
- **observability**: OpenTelemetry tracing/metrics configuration

### Tool Types
- **vectorstore**: ChromaDB-backed semantic search over documents
- **mcp**: Model Context Protocol servers for external capabilities

### Evaluation Metrics
- **GEval**: LLM-as-judge with custom criteria
- **RAG**: faithfulness, answer_relevancy, contextual_relevancy
- **Standard**: F1, BLEU, ROUGE, METEOR

## Provider Differences

| Provider | Model | Embeddings | Notes |
|----------|-------|------------|-------|
| OpenAI | gpt-4o | text-embedding-3-small | Requires OPENAI_API_KEY |
| Azure OpenAI | gpt-4o | text-embedding-ada-002 | Requires Azure credentials |
| Ollama | llama3.1:8b | nomic-embed-text | Local, no API keys |

## When Modifying Samples

1. **Always use `@schemas/agent.schema.json`** when writing or editing YAML files for schema validation
2. Changes should be consistent across all three provider variants of a sample
3. Update `.env.example` if new environment variables are needed
4. Run `holodeck test agent.yaml` to verify evaluations pass
