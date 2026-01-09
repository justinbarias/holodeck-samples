# Ticket Routing Sample - Azure OpenAI

AI-powered ticket classification and routing system using Azure OpenAI GPT-4o.

## Overview

This sample demonstrates HoloDeck's capabilities for ticket routing using Azure OpenAI as the LLM provider.

## Quick Start

### 1. Start Infrastructure

```bash
cd /samples
./start-infra.sh
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials:
# - AZURE_OPENAI_ENDPOINT
# - AZURE_OPENAI_API_KEY
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

## Azure OpenAI Setup

1. Create an Azure OpenAI resource in Azure Portal
2. Deploy a GPT-4o model
3. Copy the endpoint URL and API key
4. Add them to your `.env` file

## Files

| File | Description |
|------|-------------|
| `agent.yaml` | Agent config with Azure OpenAI provider |
| `config.yaml` | Azure OpenAI settings |
| `data/` | Category definitions and sample tickets |
| `copilotkit/` | Next.js frontend |

See the OpenAI variant's README for detailed usage instructions.
