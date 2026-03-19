# Legal Assistant Agent - Claude

An AI-powered legal assistant for analyzing and answering questions about US legislation, powered by Anthropic Claude Sonnet 4.6.

## Overview

This sample demonstrates:
- **Legislation Analysis**: Accurate analysis of US legislative documents with proper citations
- **Hierarchical Document Search**: PDF-aware search that preserves document structure (sections, subsections, cross-references)
- **Hybrid Search**: Combined semantic (ChromaDB) and keyword (OpenSearch) search for comprehensive retrieval
- **Structured Citations**: Responses include section IDs, breadcrumb trails, subsection references, and cross-references
- **Filesystem Access**: MCP-based filesystem tool for direct access to supplementary data files

## Prerequisites

1. **Anthropic API Key or OAuth Token** — You need one of:
   - An `ANTHROPIC_API_KEY` from [console.anthropic.com](https://console.anthropic.com/) with Claude Sonnet access, **or**
   - A `CLAUDE_CODE_OAUTH_TOKEN` for OAuth-based authentication (see [Obtaining a Claude Code OAuth Token](#obtaining-a-claude-code-oauth-token) below)

2. **Azure OpenAI** credentials — Used for embeddings (`text-embedding-3-small`) and the context model for contextual embeddings. You need:
   - `AZURE_OPENAI_ENDPOINT` — Your Azure OpenAI resource endpoint
   - `AZURE_OPENAI_API_KEY` — Your Azure OpenAI API key
   - `AZURE_OPENAI_DEPLOYMENT_NAME` — The deployment name for the chat model
   - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` — The deployment name for the embedding model

3. **OpenAI API Key** (optional) — Only needed if switching to OpenAI for embeddings or evaluation models

4. **Infrastructure** (from repository root):
   ```bash
   ./start-infra.sh
   ```
   This starts:
   - **ChromaDB** at http://localhost:8000 (vector store for semantic search)
   - **OpenSearch** at https://localhost:9200 (keyword index for hybrid search)
   - **Aspire Dashboard** at http://localhost:18888 (observability UI)

5. **Node.js 18+** — Required for the MCP filesystem server

### Obtaining a Claude Code OAuth Token

The `CLAUDE_CODE_OAUTH_TOKEN` is used for OAuth-based authentication with Anthropic's API (as an alternative to a standard API key). To obtain one:

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) CLI
2. Run `claude` and complete the OAuth login flow in your browser
3. After authentication, the token is stored locally. Retrieve it with:
   ```bash
   cat ~/.claude/credentials.json
   ```
4. Copy the `oauth_token` value and set it as `CLAUDE_CODE_OAUTH_TOKEN` in your `.env` file

> **Note**: If using a standard `ANTHROPIC_API_KEY` instead, update `auth_provider` in `agent.yaml` from `oauth_token` to `api_key`.

## Setup

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Start the agent**:
   ```bash
   holodeck serve agent.yaml --port 8001
   ```

3. **Or chat interactively**:
   ```bash
   holodeck chat agent.yaml
   ```

## How It Works

1. User asks a question about the legislation (HR 8847 — the CNIMDT AIGCE STD Act)
2. The agent uses **hybrid search** (50% semantic + 50% keyword) to find relevant sections in the PDF
3. Search results include hierarchical metadata: section IDs, parent chains, subsection IDs, and cross-references
4. The agent constructs a structured response with precise citations and breadcrumb trails
5. Supplementary data files (compliance reports, analysis documents) are accessible via the filesystem tool

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `legislation_search` | Hierarchical Document | Hybrid search over HR8847 PDF with semantic + keyword retrieval |
| `filesystem` | MCP | Filesystem access to supplementary data files in `./data` |

## Data Files

| File | Description |
|------|-------------|
| `HR8847_CNIMDT_AIGCE_STD_Act.pdf` | Primary legislation document |
| `cias.md` | CIAS overview documentation |
| `cias_compliance_report.md` | Compliance analysis report |
| `cias_hr8847_noncompliance_report.txt` | Non-compliance analysis |
| `query_performance.md` | Search performance metrics |
| `supply_chain_sec.md` | Supply chain security analysis |

## Test Cases

| Test | Input | Expected Tool |
|------|-------|---------------|
| Find definitions | "What is the definition of 'covered AI system'?" | `legislation_search` |
| Section lookup | "What does Section 3 of the act cover?" | `legislation_search` |
| Requirements query | "What are the reporting requirements for federal agencies?" | `legislation_search` |

## Testing

```bash
# Run all test cases
holodeck test agent.yaml --verbose

# Output results to file
holodeck test agent.yaml --output results.md
```

## Observability

View traces and metrics in Aspire Dashboard: http://localhost:18888

**Note**: Content capture is disabled by default (`capture_content: false`) to protect confidential legal documents.

## Customization

1. **Replace legislation**: Swap `data/HR8847_CNIMDT_AIGCE_STD_Act.pdf` with your own legislative document
2. **Add supplementary data**: Place additional analysis files in `data/`
3. **Modify system prompt**: Edit `instructions/system-prompt.md` to adjust citation format or response style
4. **Tune search**: Adjust `semantic_weight` and `keyword_weight` in `agent.yaml` for your document type
5. **Adjust test cases**: Update test cases in `agent.yaml` to match your legislation

## Disclaimer

This tool is for informational purposes only and does not constitute legal advice. Always consult with a qualified attorney for specific legal questions.
