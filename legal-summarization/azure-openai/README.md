# Legal Summarization Agent - Azure OpenAI

An AI-powered legal document summarization and analysis system, powered by Azure OpenAI.

## Overview

This sample demonstrates:
- **Document Summarization**: Clear, concise summaries of complex legal documents
- **Key Information Extraction**: Parties, dates, obligations, financial terms
- **Risk Identification**: Flag unusual terms, missing protections, one-sided clauses
- **Template Comparison**: Compare clauses against standard legal templates
- **Structured Output**: JSON format for integration with legal workflows
- **Full-featured Frontend**: CopilotKit for document upload and analysis

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

3. **Create documents directory**:
   ```bash
   mkdir -p documents
   # Place documents to analyze in this directory
   ```

4. **Start the agent**:
   ```bash
   holodeck serve agent.yaml --port 8001
   ```

5. **Start the frontend**:
   ```bash
   cd copilotkit
   npm install
   npm run dev
   ```

6. **Open the UI**: http://localhost:3000

## Supported Document Types

| Document Type | Key Extractions |
|--------------|-----------------|
| NDA | Confidential info definition, obligations, term, survival period |
| Service Agreement | Scope, fees, IP ownership, liability caps, termination |
| Employment | Compensation, non-compete, IP assignment, severance |
| Commercial Lease | Rent, escalation, maintenance, default remedies |
| Software License | License scope, support SLA, warranties, liability |

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `legal_templates` | VectorStore | Standard clause definitions |
| `sample_contracts` | VectorStore | Reference contracts for context |
| `filesystem` | MCP | Access documents for analysis |
| `extract_clauses` | Prompt | Structured clause extraction |

## Evaluations

| Metric | Type | Threshold | Purpose |
|--------|------|-----------|---------|
| ROUGE | Standard | 0.6 | Summary captures key information |
| BLEU | Standard | 0.5 | Extracted terms match document |
| Completeness | G-Eval | 0.8 | All key information captured |
| LegalAccuracy | G-Eval | 0.75 | Correct legal interpretation |
| Contextual Precision | RAG | 0.7 | Relevant template retrieval |
| Faithfulness | RAG | 0.85 | Grounded in document content |

## Testing

```bash
# Run all test cases
holodeck test agent.yaml --verbose

# Run specific tags
holodeck test agent.yaml --tags nda

# Output results to file
holodeck test agent.yaml --output results.md
```

## Observability

View traces and metrics in Aspire Dashboard: http://localhost:18888

## Customization

1. **Add templates**: Update `data/legal_templates.md` with your clause templates
2. **Add samples**: Extend `data/sample_contracts.json` with reference contracts
3. **Modify analysis**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`

## Disclaimer

This tool is for informational purposes only and does not constitute legal advice.
