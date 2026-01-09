# Ticket Routing Sample - OpenAI

AI-powered ticket classification and routing system using OpenAI GPT-4o.

## Overview

This sample demonstrates HoloDeck's capabilities for:
- **Agent Definition**: YAML-based configuration with structured output
- **Evaluation**: GEval metrics for classification accuracy
- **Observability**: OpenTelemetry tracing with Aspire Dashboard
- **Serving**: AG-UI protocol with CopilotKit frontend

## Quick Start

### 1. Start Infrastructure

From the `/samples` directory:

```bash
./start-infra.sh
```

This starts:
- ChromaDB (vector store) at http://localhost:8000
- Aspire Dashboard (observability) at http://localhost:18888

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the Agent

```bash
# Test the agent
holodeck test agent.yaml --verbose

# Or serve for interactive use
holodeck serve agent.yaml --port 8000
```

### 4. Start Frontend (Optional)

```bash
cd copilotkit
npm install
npm run dev
# Open http://localhost:3000
```

## How It Works

### Classification Process

1. User submits a support ticket
2. Agent searches category definitions in the vector store
3. Agent analyzes the ticket content for keywords, sentiment, and context
4. Returns structured classification with category, urgency, department, and confidence

### Sample Input

```
I was charged twice for my subscription last month. Order #12345. Please refund immediately.
```

### Sample Output

```json
{
  "category": "billing",
  "urgency": "high",
  "routing_department": "Finance Support",
  "confidence_score": 0.95,
  "reasoning": "The ticket mentions double charges and requests an immediate refund, indicating a billing issue with high urgency."
}
```

## Files

| File | Description |
|------|-------------|
| `agent.yaml` | Main agent configuration |
| `config.yaml` | OpenAI provider settings |
| `instructions/system-prompt.md` | Agent instructions |
| `data/ticket_categories.json` | Category definitions for routing |
| `data/sample_tickets.json` | Sample tickets for testing |
| `copilotkit/` | Next.js frontend |

## Evaluation Metrics

- **ClassificationAccuracy** (threshold: 0.8): Category matches expected
- **UrgencyAssessment** (threshold: 0.75): Urgency level is appropriate
- **ReasoningQuality** (threshold: 0.7): Reasoning is clear and logical
- **Faithfulness** (threshold: 0.7): Response is grounded in retrieved data

## Observability

View traces and metrics in Aspire Dashboard:
- Open http://localhost:18888
- Traces show the full request flow including vector search and LLM calls

## Customization

### Add New Categories

Edit `data/ticket_categories.json` to add new categories:

```json
{
  "category_id": "custom",
  "name": "Custom Category",
  "description": "Description of when to use this category",
  "keywords": ["keyword1", "keyword2"],
  "routing_department": "Custom Team",
  "sla_hours": 24
}
```

### Adjust Model Settings

Edit `agent.yaml`:

```yaml
model:
  provider: openai
  name: gpt-4o-mini  # Use a faster/cheaper model
  temperature: 0.0   # More deterministic
```
