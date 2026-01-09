# HoloDeck Samples

Comprehensive examples showcasing HoloDeck's core capabilities for building, testing, and deploying AI agents through pure YAML configuration.

## Overview

This directory contains 4 production-ready samples demonstrating HoloDeck's features:

| Sample | Description | Key Features |
|--------|-------------|--------------|
| [Ticket Routing](./ticket-routing/) | Classify and route support tickets | Structured output, classification, confidence scoring |
| [Customer Support](./customer-support/) | Context-aware support chatbot | RAG, conversation memory, escalation workflows |
| [Content Moderation](./content-moderation/) | Filter user-generated content | Multi-category classification, policy enforcement |
| [Legal Summarization](./legal-summarization/) | Summarize legal documents | Document analysis, clause extraction, risk identification |

Each sample is available for 3 LLM providers:
- **OpenAI** (gpt-4o) - Cloud-based, highest quality
- **Azure OpenAI** (gpt-4o) - Enterprise cloud with compliance
- **Ollama** (llama3.1:8b) - 100% local, no API keys required

## Prerequisites

### Install HoloDeck CLI

HoloDeck requires Python 3.10+ and uv (the fast Python package installer).

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: brew install uv

# Install HoloDeck with ChromaDB support
uv tool install "holodeck-ai[chromadb]@latest" --prerelease allow --python 3.10

# Verify installation
holodeck --version
```

### Additional Requirements

- **Docker** - For running ChromaDB and Aspire Dashboard
- **Node.js 18+** - For CopilotKit frontend
- **LLM Provider** - API keys for OpenAI/Azure, or Ollama for local
- **VS Code** (recommended) - Install the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) for schema validation and autocomplete in agent.yaml files

## Quick Start

### 1. Start Infrastructure

All samples require ChromaDB (vector store) and Aspire Dashboard (observability):

```bash
cd samples
./start-infra.sh
```

This starts:
- **ChromaDB** at http://localhost:8000
- **Aspire Dashboard** at http://localhost:18888 (OTLP at 4317)

### 2. Choose a Sample and Provider

```bash
cd ticket-routing/openai  # or azure-openai, ollama
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (not needed for Ollama)
```

### 4. Start the Agent

```bash
holodeck serve agent.yaml --port 8001
```

### 5. Start the Frontend

```bash
cd copilotkit
npm install
npm run dev
```

Open http://localhost:3000

## Infrastructure

### Docker Compose Services

```yaml
services:
  chromadb:       # Vector store at http://localhost:8000
  aspire-dashboard:  # OpenTelemetry UI at http://localhost:18888
```

### Start/Stop Commands

```bash
./start-infra.sh  # Start all infrastructure
./stop-infra.sh   # Stop all infrastructure
```

## Sample Directory Structure

Each sample follows this structure:

```
<use-case>/<provider>/
├── agent.yaml              # Agent configuration
├── config.yaml             # Provider-specific config
├── .env.example            # Environment template
├── README.md               # Sample documentation
├── instructions/
│   └── system-prompt.md    # Agent instructions
├── data/
│   └── *.json, *.md        # Knowledge base data
└── copilotkit/             # Next.js frontend
    ├── src/app/
    ├── package.json
    └── ...
```

## Provider Comparison

| Feature | OpenAI | Azure OpenAI | Ollama |
|---------|--------|--------------|--------|
| Model | gpt-4o | gpt-4o | llama3.1:8b |
| Embeddings | text-embedding-3-small | text-embedding-ada-002 | nomic-embed-text |
| API Key | Required | Required | None |
| Privacy | Cloud | Enterprise Cloud | 100% Local |
| Latency | Low | Low | Hardware dependent |
| Evaluation Thresholds | Standard | Standard | Slightly lower |

## HoloDeck Features Demonstrated

### Agent Definition
- Multi-provider LLM configuration
- System prompts from files
- Structured response formats
- Temperature and token limits

### Tools
- **VectorStore**: RAG with ChromaDB for knowledge retrieval
- **MCP**: Model Context Protocol for external services
- **Prompt**: Templated prompts for structured operations

### Evaluations
- **Standard Metrics**: F1, BLEU, ROUGE, METEOR
- **RAG Metrics**: Faithfulness, Answer Relevancy, Contextual Precision
- **G-Eval**: Custom LLM-as-judge evaluations

### Observability
- OpenTelemetry traces, metrics, and logs
- Aspire Dashboard visualization
- Per-request tracing

### Testing
```bash
holodeck test agent.yaml --verbose
holodeck test agent.yaml --tags <tag>
holodeck test agent.yaml --output results.md
```

## Sample Details

### Ticket Routing
Classifies customer support tickets by category and urgency.

**Response Format:**
```json
{
  "category": "billing|technical|sales|account|general",
  "urgency": "critical|high|medium|low",
  "routing_department": "...",
  "confidence_score": 0.95,
  "reasoning": "..."
}
```

**Evaluations:** Classification accuracy, confidence calibration

---

### Customer Support
Context-aware chatbot with knowledge base and FAQ lookup.

**Tools:**
- `knowledge_base` - Product documentation
- `faq` - Frequently asked questions
- `memory` - Conversation persistence
- `escalate_to_human` - Escalation templates

**Evaluations:** Faithfulness, helpfulness, professionalism

---

### Content Moderation
Classifies user content against community guidelines.

**Categories:** Hate speech, harassment, violence, misinformation, adult content, spam, illegal activities

**Response Format:**
```json
{
  "decision": "approve|warning|remove|suspend|escalate",
  "violations": [...],
  "reasoning": "...",
  "confidence_score": 0.9
}
```

**Evaluations:** Moderation accuracy, reasoning quality, consistency

---

### Legal Summarization
Analyzes and summarizes legal documents.

**Tools:**
- `legal_templates` - Standard clause definitions
- `sample_contracts` - Reference contracts
- `filesystem` - Document access
- `extract_clauses` - Structured extraction

**Evaluations:** ROUGE, BLEU, completeness, legal accuracy

## Ollama Setup

For local LLM samples:

```bash
# Install Ollama
brew install ollama

# Start Ollama
ollama serve

# Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text:latest
```

## Troubleshooting

### "holodeck: command not found"
```bash
# Ensure uv tools are in PATH
export PATH="$HOME/.local/bin:$PATH"

# Reinstall HoloDeck
uv tool install "holodeck-ai[chromadb]@latest" --prerelease allow --python 3.10 --force
```

### ChromaDB not starting
```bash
docker logs holodeck-chromadb
```

### Aspire Dashboard not accessible
```bash
docker logs holodeck-aspire
```

### Vector store errors
Ensure ChromaDB is healthy before initializing:
```bash
curl http://localhost:8000/api/v2/heartbeat
```

### Ollama connection refused
```bash
ollama serve  # Ensure Ollama is running
curl http://localhost:11434/api/version  # Verify connection
```

## Next Steps

1. **Customize a sample** - Modify prompts, add data, adjust evaluations
2. **Add new providers** - Copy an existing variant and update configs
3. **Build your own** - Use these samples as templates for new use cases
4. **Deploy** - Use `holodeck deploy` for production deployment

## Claude Code Integration

This repository includes slash commands for [Claude Code](https://claude.ai/code) to streamline agent development. These commands provide guided, conversational workflows for creating and optimizing HoloDeck agents.

### Available Slash Commands

| Command | Description |
|---------|-------------|
| `/holodeck.create` | Conversational wizard to scaffold and configure a new agent |
| `/holodeck.tune` | Iteratively tune an existing agent to improve test performance |

### /holodeck.create

A step-by-step wizard that guides you through creating a new HoloDeck agent:

1. **Basic Information** - Agent name, description, use case category, LLM provider
2. **Model Configuration** - Temperature, max tokens based on use case
3. **System Prompt Design** - Role, guidelines, process, output format
4. **Response Format** - JSON schema for structured output (if needed)
5. **Tools Configuration** - Vectorstore (RAG), MCP servers
6. **Evaluation Metrics** - RAG metrics, GEval custom criteria
7. **Test Cases** - Comprehensive test scenarios
8. **Observability** - OpenTelemetry configuration
9. **Finalization** - Validation and next steps

**Usage:**
```
/holodeck.create
```

The wizard will ask clarifying questions at each phase before proceeding.

### /holodeck.tune

An iterative tuning assistant that improves agent test performance:

1. **Initial Assessment** - Runs baseline tests, records pass/fail rates
2. **Diagnosis** - Analyzes failures and identifies root causes
3. **Tuning Loop** - Proposes changes, applies them, measures improvement
4. **Changelog Tracking** - Records all modifications in `changelog.md`

**What it CAN modify:**
- System prompt content
- Model settings (temperature, max_tokens)
- Tool configuration (top_k, chunk_size, min_similarity_score)
- Evaluation thresholds

**What it CANNOT modify:**
- Test cases (inputs, ground_truth, expected_tools)
- Agent name and description

**Usage:**
```
/holodeck.tune path/to/agent.yaml
```

The tuner will ask for maximum iterations and priority tests before starting.

### Command Files Location

The slash commands are defined in:
```
.claude/commands/
├── holodeck.create.md    # Agent creation wizard
└── holodeck.tune.md      # Agent tuning assistant
```

## GitHub Copilot Integration

This repository also includes prompt files for [GitHub Copilot](https://github.com/features/copilot) in VS Code, Visual Studio, and JetBrains IDEs. These prompts provide the same guided workflows as the Claude Code commands.

### Available Prompts

| Prompt | Description |
|--------|-------------|
| `holodeck-create` | Conversational wizard to scaffold and configure a new agent |
| `holodeck-tune` | Iteratively tune an existing agent to improve test performance |

### How to Use

1. Open the repository in VS Code (or supported IDE) with GitHub Copilot Chat
2. Type `/` in the chat input to see available prompts
3. Select `holodeck-create` or `holodeck-tune`
4. Follow the conversational wizard

Alternatively, type `#prompt:` and select the prompt from the dropdown.

### holodeck-create

A step-by-step wizard that guides you through creating a new HoloDeck agent:

1. **Basic Information** - Agent name, description, use case category, LLM provider
2. **Model Configuration** - Temperature, max tokens based on use case
3. **System Prompt Design** - Role, guidelines, process, output format
4. **Response Format** - JSON schema for structured output (if needed)
5. **Tools Configuration** - Vectorstore (RAG), MCP servers
6. **Evaluation Metrics** - RAG metrics, GEval custom criteria
7. **Test Cases** - Comprehensive test scenarios
8. **Observability** - OpenTelemetry configuration
9. **Finalization** - Validation and next steps

### holodeck-tune

An iterative tuning assistant that improves agent test performance:

1. **Initial Assessment** - Analyzes baseline test results
2. **Diagnosis** - Identifies failure patterns and root causes
3. **Tuning Loop** - Proposes changes, guides you through applying them
4. **Changelog Tracking** - Helps maintain `changelog.md` with all modifications

### Prompt Files Location

The GitHub Copilot prompts are defined in:
```
.github/prompts/
├── holodeck-create.prompt.md    # Agent creation wizard
└── holodeck-tune.prompt.md      # Agent tuning assistant
```

> **Note:** GitHub Copilot prompts provide guidance-focused workflows. Unlike Claude Code commands which can execute tools directly, Copilot prompts suggest commands for you to run manually.

## Resources

- [Installation Guide](https://docs.useholodeck.ai/getting-started/installation)
- [HoloDeck Documentation](https://docs.useholodeck.ai)
- [Agent Configuration](https://docs.useholodeck.ai/guides/agent-configuration)
- [Evaluation Framework](https://docs.useholodeck.ai/guides/evaluation)
- [Tool Types](https://docs.useholodeck.ai/guides/tools)
