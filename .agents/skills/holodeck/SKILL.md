---
name: holodeck
description: Helps developers work with HoloDeck — the open-source no-code YAML agent platform (CLI `holodeck`, schema `agent.yaml`, docs at https://docs.useholodeck.ai/). Use this skill whenever the user is creating, evaluating, or deploying a HoloDeck agent, even if they don't say "holodeck" explicitly. Strong triggers include phrases like "set up an agent.yaml", "scaffold an agent", "build an experiment", "write evaluations / graders / test cases", "analyze the test results", "open the holodeck dashboard", "deploy this agent", "holodeck deploy build|run", "ship to Azure / Cloud Run / Container Apps", and any reference to `agent.yaml`, `agent.schema.json`, `holodeck.lib`, `holodeck-base`, or the docsite host `docs.useholodeck.ai`. Operates in three modes — bootstrap, refine, ship — covering the full agent lifecycle.
---

# HoloDeck workflow skill

This skill helps the user move an agent through HoloDeck's three-stage lifecycle: **bootstrap → refine → ship**. Each stage has its own playbook in `references/`.

The authoritative source of truth is the live docsite at `https://docs.useholodeck.ai/`. The skill reference files describe the *workflow*; the docsite describes the *API*. When the user asks something concrete (a field name, a flag, a JSON schema constraint), prefer the docsite over your training data.

## Always start here: pull the live docs index

```
https://docs.useholodeck.ai/llms.txt
```

That file is a curated TOC with absolute URLs to every guide and API reference. The full markdown corpus is at `https://docs.useholodeck.ai/llms-full.txt` (~1.6 MB). When you need a specific page, fetch it from the URL in `llms.txt` — don't guess paths.

The most-used pages by mode:

| Mode | Primary references on the docsite |
|---|---|
| bootstrap | `/guides/agent-configuration/`, `/getting-started/quickstart/`, `/guides/tools/`, `/guides/llm-providers/` |
| refine | `/guides/evaluations/`, `/guides/dashboard/`, `/api/evaluators/`, `/api/test-runner/` |
| ship | `/guides/deployment/`, `/guides/serve/`, `/guides/claude-backend/` (production-considerations section) |

## Dispatch: which mode are we in?

Two ways to enter a mode — **explicit override wins**:

1. **Explicit override.** If the user mentions a mode by name ("help me bootstrap an agent", "let's get into refine", "I want to ship this"), use that.
2. **Auto-detect from intent.** Otherwise infer from cues:
   - *No agent.yaml yet*, or talk about scaffolding, ideas, picking a model/provider → `bootstrap`
   - *Has an agent.yaml, talking about test cases, graders, scores, results.json, dashboard* → `refine`
   - *Wants to deploy, build a docker image, run on Azure / Cloud Run / ECS, push to a registry* → `ship`

When the cues are mixed (e.g. "help me write a grader for my deploy validation"), say what you think the active mode is in one sentence and let the user correct you.

## Read the mode playbook before doing anything

After picking a mode, **read the matching reference file** before suggesting actions:

- `references/bootstrap.md` — scaffolding a new `agent.yaml` from scratch
- `references/refine.md` — evaluations, graders, dashboard, test-result analysis
- `references/ship.md` — building images, picking a deploy runtime, `holodeck deploy build|run`

Each reference is self-contained — no need to load all three.

## Cross-cutting principles

These apply regardless of mode:

1. **YAML is the source of truth, not chat.** When the user describes a desired behaviour, the next step is usually to edit `agent.yaml`. Show the diff, don't just narrate.

2. **Validate before running.** Run `holodeck config validate <path>` (or `holodeck test --dry-run`) before spending tokens on a real LLM call. Catches schema regressions and missing env vars cheaply.

3. **Secrets stay in `.env`.** Never paste a real key into `agent.yaml`; use `${VAR_NAME}` interpolation. If the user shares a key in chat, flag it and recommend rotation — don't store it.

4. **Use `${VAR_NAME}` for anything tenant-specific.** Subscription IDs, registry URLs, model deployment names — anything another developer would need to change should be an env var with a placeholder in `.env.sample`.

5. **Pin to the canonical schema.** `schemas/agent.schema.json` (also published in the `holodeck-samples` repo) is the authoritative shape. If the user's editor isn't validating against it, suggest setting up a `yaml-language-server` modeline:
   ```yaml
   # yaml-language-server: $schema=https://docs.useholodeck.ai/schemas/agent.schema.json
   ```

6. **Stop early when context is unclear.** Don't generate a 200-line `agent.yaml` from one sentence — ask one targeted question (provider? task domain? data source?) and then proceed. The user fixing one wrong assumption is cheaper than rewriting half the file.

## End-of-task sanity check

Before declaring a task done in any mode, confirm one of these:

- **bootstrap**: `holodeck config validate <path>` passes AND `holodeck chat --once "hello"` returns a non-error response.
- **refine**: `holodeck test` ran, the JSON report exists under `results/`, and at least one assertion explains *why* a turn passed or failed.
- **ship**: `holodeck deploy run` returned `Status: Succeeded` AND `curl -sf $URL/health` returns 200 with `agent_ready: true`.

If none of those hold, the work isn't done — say so explicitly rather than reporting success.

## When in doubt

Surface the assumption you're about to make and let the user correct you. This skill biases toward speed because HoloDeck's iteration loop is tight, but a wrong scaffold or a wrong deployment target costs more than a 30-second clarifying question.
