# Customer Support Sample - OpenAI

AI-powered customer support agent using OpenAI GPT-4o with RAG-based knowledge retrieval.

## Overview

This sample demonstrates:
- **RAG Integration**: Knowledge base and FAQ search with ChromaDB
- **Conversational AI**: Natural, helpful customer interactions
- **Memory**: Conversation context retention with MCP
- **Evaluation**: RAG metrics (faithfulness, relevancy) + custom GEval

## Quick Start

### 1. Start Infrastructure

```bash
cd /samples
./start-infra.sh
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run the Agent

```bash
holodeck test agent.yaml --verbose
# Or serve for interactive use
holodeck serve agent.yaml --port 8000
```

### 4. Start Frontend

```bash
cd copilotkit
npm install
npm run dev
# Open http://localhost:3000
```

## How It Works

1. Customer asks a question
2. Agent searches knowledge base and FAQ using semantic search
3. Agent synthesizes response from retrieved context
4. Memory tool retains conversation history for follow-up questions

## Sample Interaction

**Customer:** "How do I reset my password?"

**Agent:** "Hi there! I'd be happy to help you reset your password. Here's how:

1. Go to the login page
2. Click 'Forgot Password'
3. Enter your email address
4. Check your email for the reset link

If you don't receive the email within 5 minutes, check your spam folder. Is there anything else I can help you with?"

## Files

| File | Description |
|------|-------------|
| `agent.yaml` | Agent configuration |
| `data/knowledge_base.md` | Product documentation (~2000 words) |
| `data/faq.json` | Frequently asked questions |
| `data/product_catalog.json` | Product and pricing info |

## Evaluation Metrics

- **Faithfulness** (0.8): Response grounded in retrieved context
- **Answer Relevancy** (0.75): Response relevant to question
- **Contextual Relevancy** (0.7): Retrieved context is relevant
- **Helpfulness** (0.8): Response is actionable and complete
- **Professionalism** (0.7): Appropriate tone and language

## Customization

### Add Knowledge
Edit `data/knowledge_base.md` to add product documentation.

### Add FAQs
Add entries to `data/faq.json`:
```json
{
  "id": "faq_new",
  "question": "Your question here",
  "answer": "Detailed answer here",
  "category": "category",
  "keywords": ["keyword1", "keyword2"]
}
```
