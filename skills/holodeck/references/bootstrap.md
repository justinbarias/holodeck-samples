# Mode: bootstrap

You're helping a developer go from "I want an agent that does X" to a runnable `agent.yaml`. The goal is the **smallest real config** that proves the agent can answer one prompt — not a perfect production setup.

## What to find out first (one question, max two)

You usually need only one or two of these. Don't survey — pick whichever is *blocking* and ask just that.

1. **What's the agent supposed to do?** A one-sentence task description grounds every later choice. ("Answer questions about our internal API docs", "Generate SQL from natural language against the analytics warehouse", etc.)
2. **Which provider?** Default to `anthropic` (Claude is HoloDeck's first-class backend). Switch to `openai`, `azure_openai`, or `ollama` if the user names them or has an obvious credentials story (e.g. corporate Azure tenant).
3. **What data does it touch?** If "none, it's pure reasoning" → no tools. If "a folder of PDFs / a Confluence space / a SQL DB" → that drives the tool type (see below).

If the user already volunteered all three in their prompt, skip the question and write the file.

## Picking a tool type

HoloDeck supports six tool types. Choose by **what the agent needs to do**, not by what sounds fanciest:

| Need | Tool type | Why |
|---|---|---|
| Static reference corpus (docs, PDFs, knowledge base) | `vectorstore` | Semantic retrieval, cheap to set up. |
| Large hierarchical doc (manual, contract, spec) | `hierarchical_document` | Preserves section structure; supports hybrid (semantic + keyword) search. Best when one section's meaning depends on its siblings. |
| Deterministic computation (math, parsing, formatting) | `function` | Plain Python callable. No retrieval; the LLM picks args. |
| External API (GitHub, Slack, JIRA, etc.) | `mcp` | MCP server (stdio or HTTP) — never write a custom API tool type. |
| Reusable prompt template | `prompt` | The agent can invoke a named prompt as a tool. |
| Lower-level integration / custom logic | `plugin` | Last resort; prefer `function` or `mcp`. |

For Anthropic agents that use a `vectorstore` or `hierarchical_document` tool, the user **also** needs an `embedding_provider:` block (Claude doesn't ship native embeddings). Azure OpenAI's `text-embedding-3-small` is a reasonable default. Flag this — it's the #1 first-run failure.

## Scaffold paths

Two ways to start, depending on the situation:

### Option A: `holodeck init` (preferred when there's a template)

```bash
holodeck init <name> --template <template-name>
```

`holodeck init --list-templates` shows what's available. The financial-assistant sample in `holodeck-samples/financial-assistant/claude/` is also a usable template — copy it and rip out the ConvFinQA-specific bits.

### Option B: Hand-write a minimal `agent.yaml`

When no template fits, write the file directly. Keep it short — *runnable first, polished later*. A minimal Anthropic agent:

```yaml
# yaml-language-server: $schema=https://docs.useholodeck.ai/schemas/agent.schema.json
name: my-agent
description: One-sentence purpose.
model:
  provider: anthropic
  name: claude-sonnet-4-6
  auth_provider: oauth_token   # or api_key, if using ANTHROPIC_API_KEY
instructions:
  inline: |
    You are a [role]. Help the user with [task]. Cite sources when relevant.
```

Add tools only when you've confirmed the agent needs them. Each tool you add is one more failure mode to debug.

## Environment

Always create both files at the same time:

- `.env` — real values, gitignored
- `.env.sample` — placeholders, committed

Standard vars by provider:

| Provider | Required env vars |
|---|---|
| anthropic (api_key) | `ANTHROPIC_API_KEY` |
| anthropic (oauth_token) | `CLAUDE_CODE_OAUTH_TOKEN` |
| openai | `OPENAI_API_KEY` |
| azure_openai | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME` (+ `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` if embeddings used) |
| ollama | `OLLAMA_BASE_URL` (default `http://localhost:11434`) |

Auth priority at runtime is: shell env > `.env` (project) > `~/.holodeck/.env` (user). Mention this if the user is surprised their key isn't picked up.

## First-run validation loop

Before moving on, prove the agent loads and answers:

```bash
holodeck config validate agent.yaml    # schema check, no LLM call
holodeck chat --once "hello, who are you?"   # one round-trip
```

If `holodeck config validate` fails, the error names the offending field — fix that first, don't try to debug at runtime.

If `holodeck chat` fails with a credentials error, walk the user through `.env` setup; don't assume the key is wrong.

## Common bootstrap traps

| Symptom | Cause / fix |
|---|---|
| `Extra inputs are not permitted: <field>` | The installed `holodeck` CLI is older than the YAML's schema. Reinstall: `uv tool install --reinstall --prerelease=allow --from <repo-root> --with docker holodeck-ai`. |
| `embedding_provider` required error | Anthropic agent has a vectorstore/hierarchical_document tool but no embeddings configured — add the block. |
| Tool descriptions ignored | Tool `description:` is the most-overlooked field; the LLM's tool routing depends on it. Make it imperative and specific. |
| Mutable defaults in Python `function` tools | Use `None` and rebuild, never `[]`/`{}`. |

## When done with bootstrap

Hand off to `refine` mode by recommending the next step explicitly: "You have a runnable agent. Want to write some test cases so you can iterate without manual chat?" That's the natural transition into [[refine]].

## Authoritative references (always fetch fresh)

- `https://docs.useholodeck.ai/getting-started/quickstart/`
- `https://docs.useholodeck.ai/guides/agent-configuration/`
- `https://docs.useholodeck.ai/guides/llm-providers/`
- `https://docs.useholodeck.ai/guides/tools/`
- `https://docs.useholodeck.ai/guides/file-references/` (for file path resolution rules)
- `schemas/agent.schema.json` (in the agentlab repo or holodeck-samples)
