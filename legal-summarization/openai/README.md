# Legal Summarization Agent - OpenAI

An AI-powered legal document summarization and analysis system, powered by OpenAI GPT-4o.

## Overview

This sample demonstrates:
- **Document Summarization**: Clear, concise summaries of complex legal documents
- **Key Information Extraction**: Parties, dates, obligations, financial terms
- **Risk Identification**: Flag unusual terms, missing protections, one-sided clauses
- **Template Comparison**: Compare clauses against standard legal templates
- **Structured Output**: JSON format for integration with legal workflows
- **Full-featured Frontend**: CopilotKit for document upload and analysis

## Prerequisites

1. **OpenAI API Key** with GPT-4o access

2. **Infrastructure** (from `/samples` root):
   ```bash
   ./start-infra.sh
   ```

3. **Node.js 18+** for CopilotKit frontend

## Setup

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Create documents directory**:
   ```bash
   mkdir -p documents
   # Place documents to analyze in this directory
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

## Supported Document Types

| Document Type | Key Extractions |
|--------------|-----------------|
| NDA | Confidential info definition, obligations, term, survival period |
| Service Agreement | Scope, fees, IP ownership, liability caps, termination |
| Employment | Compensation, non-compete, IP assignment, severance |
| Commercial Lease | Rent, escalation, maintenance, default remedies |
| Software License | License scope, support SLA, warranties, liability |

## Response Format

```json
{
  "summary": "Executive summary (2-3 paragraphs)",
  "document_type": "NDA|Service|Employment|Lease|License",
  "parties": [
    {
      "name": "Company Inc.",
      "role": "Licensor",
      "obligations": ["Provide software", "Maintain 99.9% uptime"]
    }
  ],
  "key_clauses": [
    {
      "name": "Limitation of Liability",
      "summary": "Caps liability at 12 months of fees",
      "assessment": "standard",
      "risk_level": "low"
    }
  ],
  "key_dates": [
    {"description": "Effective Date", "date": "2024-01-15"},
    {"description": "Term", "date": "3 years"}
  ],
  "risks_identified": [
    {
      "description": "Unlimited indemnification for IP claims",
      "severity": "high",
      "clause_reference": "Section 8.1",
      "recommendation": "Negotiate cap on indemnification"
    }
  ]
}
```

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

**Note**: Content capture is disabled by default to protect confidential legal documents.

## Data Files

- `data/legal_templates.md` - Standard clause definitions (3000+ words)
- `data/sample_contracts.json` - 5 sample contracts for reference

## Customization

1. **Add templates**: Update `data/legal_templates.md` with your clause templates
2. **Add samples**: Extend `data/sample_contracts.json` with reference contracts
3. **Modify analysis**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`

## Disclaimer

This tool is for informational purposes only and does not constitute legal advice. Always consult with a qualified attorney for important legal decisions.
