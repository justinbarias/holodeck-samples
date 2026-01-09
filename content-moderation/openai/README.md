# Content Moderation Agent - OpenAI

An AI-powered content moderation system for classifying and filtering user-generated content, powered by OpenAI GPT-4o.

## Overview

This sample demonstrates:
- **Policy-Based Moderation**: RAG-powered policy lookup from community guidelines
- **Structured Decisions**: JSON output with categories, severity, and reasoning
- **Multi-Category Classification**: 7 violation categories with subcategories
- **Quality Evaluations**: G-Eval for accuracy, reasoning quality, and consistency
- **RAG Faithfulness**: Ensure decisions are grounded in actual policies
- **Full-featured Frontend**: CopilotKit for content review interface

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

2. **Initialize vector stores** (first run):
   ```bash
   holodeck init-vectors agent.yaml
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

## Response Format

```json
{
  "decision": "approve|warning|remove|suspend|escalate",
  "violations": [
    {
      "category": "harassment",
      "subcategory": "direct_harassment",
      "severity": "medium",
      "evidence": "specific violating text"
    }
  ],
  "reasoning": "Clear explanation of the decision",
  "recommended_action": "Specific action to take",
  "confidence_score": 0.88
}
```

## Tools

| Tool | Type | Description |
|------|------|-------------|
| `moderation_rules` | VectorStore | Community guidelines and policies |
| `category_definitions` | VectorStore | Violation categories and examples |
| `analyze_content` | Prompt | Deep analysis for nuanced cases |

## Evaluations

| Metric | Type | Threshold | Purpose |
|--------|------|-----------|---------|
| ModerationAccuracy | G-Eval | 0.85 | Correct violation classification |
| ReasoningQuality | G-Eval | 0.75 | Clear, useful explanations |
| Faithfulness | RAG | 0.8 | Grounded in actual policies |
| Consistency | G-Eval | 0.8 | Same content gets same decision |

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

**Note**: Content capture is disabled by default to avoid logging potentially harmful content.

## Data Files

- `data/moderation_rules.md` - Full community guidelines (1500+ words)
- `data/category_definitions.json` - 7 categories with subcategories and examples

## Customization

1. **Add policies**: Update `data/moderation_rules.md` with your guidelines
2. **Add categories**: Extend `data/category_definitions.json`
3. **Modify persona**: Edit `instructions/system-prompt.md`
4. **Adjust thresholds**: Update evaluation thresholds in `agent.yaml`
5. **Lower temperature**: Currently at 0.1 for consistency

## Security Considerations

- Never log full content of flagged materials
- Implement rate limiting for abuse prevention
- Consider human-in-the-loop for critical decisions
- Regularly audit decisions for bias
