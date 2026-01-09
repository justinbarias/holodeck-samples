# Content Moderation Agent - Ollama

An AI-powered content moderation system for classifying and filtering user-generated content, powered by Ollama (local LLM).

## Overview

This sample demonstrates:
- **Policy-Based Moderation**: RAG-powered policy lookup from community guidelines
- **Structured Decisions**: JSON output with categories, severity, and reasoning
- **Multi-Category Classification**: 7 violation categories with subcategories
- **Quality Evaluations**: G-Eval for accuracy, reasoning quality, and consistency
- **RAG Faithfulness**: Ensure decisions are grounded in actual policies
- **Full-featured Frontend**: CopilotKit for content review interface
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

## Violation Categories

| Category | Severity | Auto-Remove | Description |
|----------|----------|-------------|-------------|
| Hate Speech | High | Yes | Discrimination against protected groups |
| Harassment | High | No | Targeting individuals to intimidate |
| Violence | Critical | Yes | Threats or glorification of violence |
| Misinformation | Medium | No | False information with harm potential |
| Adult Content | High | Yes | Sexually explicit material |
| Spam | Low | No | Inauthentic or manipulative content |
| Illegal Activities | Critical | Yes | Content facilitating crimes |

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `moderation_rules` | VectorStore | Community guidelines and policies |
| `category_definitions` | VectorStore | Violation categories and examples |
| `analyze_content` | Prompt | Deep analysis for nuanced cases |

## Evaluations

Note: Thresholds are slightly lower for local models compared to cloud providers.

| Metric | Type | Threshold | Purpose |
|--------|------|-----------|---------|
| ModerationAccuracy | G-Eval | 0.8 | Correct violation classification |
| ReasoningQuality | G-Eval | 0.7 | Clear, useful explanations |
| Faithfulness | RAG | 0.75 | Grounded in actual policies |
| Consistency | G-Eval | 0.75 | Same content gets same decision |

## Testing

```bash
# Run all test cases
holodeck test agent.yaml --verbose

# Run specific tags
holodeck test agent.yaml --tags harassment

# Output results to file
holodeck test agent.yaml --output results.md
```

## Observability

View traces and metrics in Aspire Dashboard: http://localhost:18888

## Hardware Requirements

- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **GPU**: Optional but improves performance significantly

## Customization

1. **Add policies**: Update `data/moderation_rules.md` with your guidelines
2. **Add categories**: Extend `data/category_definitions.json`
3. **Modify persona**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`
5. **Change model**: Swap `llama3.1:8b` for other Ollama models
