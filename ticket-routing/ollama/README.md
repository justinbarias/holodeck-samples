# Ticket Routing Sample - Ollama

AI-powered ticket classification and routing system using local Ollama with Llama 3.1.

## Overview

This sample demonstrates HoloDeck's capabilities for ticket routing using Ollama as the local LLM provider.

## Prerequisites

### Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Pull Required Models

```bash
# LLM model
ollama pull llama3.1:8b

# Embedding model
ollama pull nomic-embed-text:latest
```

## Quick Start

### 1. Start Ollama

```bash
ollama serve
```

### 2. Start Infrastructure

```bash
cd /samples
./start-infra.sh
```

### 3. Run the Agent

```bash
holodeck test agent.yaml --verbose
# Or
holodeck serve agent.yaml --port 8000
```

### 4. Start Frontend

```bash
cd copilotkit
npm install
npm run dev
```

## Notes

- Ollama runs locally, no API keys required
- First run may be slower due to model loading
- llama3.1:8b provides good classification accuracy with reasonable speed
- Use larger models (70b) for better accuracy if hardware allows

## Files

| File | Description |
|------|-------------|
| `agent.yaml` | Agent config with Ollama provider |
| `config.yaml` | Ollama settings with local endpoint |
| `data/` | Category definitions and sample tickets |
| `copilotkit/` | Next.js frontend |

See the OpenAI variant's README for detailed usage instructions.
