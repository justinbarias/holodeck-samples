# Mode: ship

You're helping a developer turn a validated agent into a running deployment. The two commands are short — `holodeck deploy build` then `holodeck deploy run` — but the choices around them (runtime, image registry, secrets, production tuning) matter and are easy to get wrong.

## Pre-flight: is this agent ready to ship?

Before touching `deploy`, confirm:

1. **`holodeck test` is green** (or known-yellow with documented exceptions). Don't deploy something you wouldn't recommend to a teammate.
2. **`.env` is complete** — every `${VAR}` in `agent.yaml` resolves. Run `holodeck config validate` and check for missing-variable errors.
3. **`deployment:` block exists in `agent.yaml`** with at least `port`, `protocol`, `platform`, `registry`, and a `target.<provider>` subtree. If it's missing, you're not ready — go back and add it (see `Deployment block` below).

If any of these fail, stop and address them first. Don't push a broken agent to prod just because the user asked you to.

## Deployment runtime — pick the right one

The user may or may not ask you to choose. If they do, the **default is Azure Container Apps** (best HoloDeck support, well-trodden path) unless they have a strong reason otherwise.

| Runtime | When it's the right choice |
|---|---|
| **Azure Container Apps** | Default. Best support; scales to zero; ingress + TLS handled. Most HoloDeck samples ship for ACA. |
| **AWS ECS / Fargate** | User is already on AWS; needs VPC isolation; corporate policy excludes Azure. |
| **GCP Cloud Run** | User is already on GCP; wants per-request billing; simple stateless agents. |
| **Generic Docker host** (Hetzner, fly.io, on-prem) | User wants control over the host; cost-sensitive; not building for scale. |
| **Local Docker** | Smoke-test only. `docker run -p 8080:8080 <image>` after `deploy build`. |

If the user names a runtime not in the list (e.g. Kubernetes), the build step is unchanged — `holodeck deploy build` produces a portable image. The `deploy run` step is what's runtime-specific; for unsupported runtimes, hand them the image URI and let them deploy it with their own tooling (kubectl, terraform, etc.).

## Deployment block in `agent.yaml`

A minimal Azure deployment block looks like this:

```yaml
deployment:
  port: 8080
  protocol: ag-ui                   # or `mcp`, `http`, depending on consumer
  platform: linux/amd64             # ACA only supports amd64; build for amd64 even on Apple Silicon
  registry:
    url: ghcr.io
    repository: <owner>/<image-name>
    tag_strategy: git_sha           # or `semver`, `latest` (avoid `latest` in prod)
  target:
    provider: azure
    azure:
      subscription_id: ${AZURE_SUBSCRIPTION_ID}    # use env vars, not literal IDs
      resource_group: holodeck-rg
      environment_name: holodeck-env
      location: eastus
      cpu: 1.0
      memory: 2Gi                   # ACA requires memory_Gi == 2 * cpu_cores
      ingress_external: true        # or `false` for internal-only
      min_replicas: 0
      max_replicas: 3
  environment:
    # Runtime secrets — resolved from operator's shell env at `deploy run` time
    # and set as Container Apps env vars. The image is shared; only this block
    # changes between deployments.
    ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    # ... other secrets ...
```

Things to call out:

- **Subscription IDs in env vars, not literals.** A literal subscription ID in a sample repo is a footgun. Always `${AZURE_SUBSCRIPTION_ID}` or similar, with the value in `.env`.
- **Memory math:** ACA requires `memory_Gi == 2 * cpu_cores`. For Claude agents, see "Production tuning" below for the implication on `session_memory_estimate_mib`.
- **`ingress_external: false`** locks the agent to the Container Apps environment's internal network. Use this for backend-only agents or while still in soak-test.

## The build → run loop

The whole loop, when the published `holodeck-base:latest` is what you want:

```bash
holodeck deploy build      # builds + tags <registry>/<repo>:<git_sha>
docker push <registry>/<repo>:<git_sha>    # CLI doesn't push automatically
holodeck deploy run        # creates/updates the runtime target
```

After `deploy run`:

```bash
URL=$(jq -r '.deployments["<agent-name>"].url' .holodeck/deployments.json)
until curl -sf -o /dev/null --max-time 5 "$URL/health"; do sleep 3; done
curl -sf "$URL/health"     # expect: {"status":"healthy", "agent_ready":true, "backend_ready":true}
```

A cold first request is normal (40–70s for Claude agents on first replica spin-up). Subsequent requests are sub-10s.

### Smoke-test the protocol

The protocol you set in `deployment.protocol` determines the endpoint shape:

- `ag-ui` → POST `/awp` with `{threadId, runId, state, messages, tools, context, forwardedProps}`. Streams SSE back.
- `mcp` → MCP over HTTP at `/mcp`.
- `http` → simple POST `/invoke` with `{input, context}`.

Send one real request before declaring success. Don't trust `/health` alone — that only proves the process is up, not that the LLM round-trips.

## When the user asks "what runtime should I use?"

Ask exactly one clarifying question — *not* a survey:

> "Do you have an existing cloud (Azure / AWS / GCP) you're standardised on, or is this a greenfield deploy?"

Then recommend:

- Existing cloud → that cloud's container service.
- Greenfield + want lowest setup → ACA.
- Greenfield + cost-sensitive + scale-to-zero matters → Cloud Run.
- Greenfield + control / cheap baseline → fly.io or Hetzner with `docker compose`.

## Production tuning (Claude backend specifically)

If `model.provider: anthropic`, the agent runs the **Claude Agent SDK** with per-turn Node CLI subprocesses (spec 034 P4 "Hybrid Sessions"). Two knobs matter at runtime:

| Field | Default | What it controls |
|---|---|---|
| `claude.session_memory_estimate_mib` | 500 | Per-active-turn memory budget. Drives the derived concurrent-turn cap from the replica's `memory:` value. |
| `claude.max_concurrent_sessions` | derived | Hard ceiling on concurrent active turns. When omitted, derived as `(memory_bytes - 400 MiB baseline) / session_memory_estimate_mib`. |

**Calibration data (from spec 034 P4 cloud validation):**

| Replica memory | Derived turn cap | Empirical safe burst | Behavior at cap |
|---|---|---|---|
| 1 GiB | 1 | 1 | extra concurrent turns return HTTP 429 |
| 2 GiB | 3 | 3 (4 OOMs) | 4 concurrent turns triggers cgroup OOMKill on ACA |
| 4 GiB | 7 | — | |
| 8 GiB | 15 | — | |

The 500 MiB default covers ~300 MiB Node CLI steady state + simultaneous-startup spikes + parent-side hybrid-search / rerank / context-generation transients. If your agent is *thin* (no parent-side retrieval, no MCP tools), you can drop it to 300 MiB and get more concurrency per replica. If it's *heavy* (multiple parent MCP tools, large per-turn embeddings), raise to 700-900 MiB.

When the cap is reached, the server **fail-fasts with HTTP 429** rather than queueing. This is intentional — Anthropic's SDK hosting guidance prefers backpressure over queueing because a queued turn ties up memory for the entire wait.

See `https://docs.useholodeck.ai/guides/claude-backend/` (Production considerations section) for the full math.

## Local-base validation loop (advanced)

When a fix in working-tree code needs end-to-end verification *before* it's published to GHCR, see `CLAUDE.md` (section: "End-to-End Deploy Validation Loop"). This involves:

1. Building a local wheel: `uv build --wheel`
2. Building a local base image: `docker buildx build -f docker/Dockerfile.local ... --load .`
3. Temporarily disabling `pull=True` in `src/holodeck/deploy/builder.py`
4. Running `holodeck deploy build` + push + `holodeck deploy run`
5. Reverting the builder.py edit

**Do not run this loop unless the user explicitly asks.** It builds + pushes + rolls a live revision. For the normal case (live base), the three-command loop in "The build → run loop" above is all you need.

## Common ship traps

| Symptom | Cause / fix |
|---|---|
| `pull access denied for ghcr.io/<owner>/<repo>` | Operator's `gh auth status` / `docker login ghcr.io` is missing. |
| `Image not found` after push | You pushed `:latest` but `tag_strategy: git_sha` — push the SHA tag. |
| `exec format error` in container logs | Built for arm64, ACA needs amd64. Add `--platform linux/amd64`. |
| `OOMKilled` (exit code 137) | Per-active-turn memory under-budgeted. Raise `session_memory_estimate_mib` or replica `memory`. |
| 429 on every request | `max_concurrent_sessions: 1` or memory derivation is 1. Check `claude.*` block. |
| `/health` 200 but real requests 502 | Backend init failed mid-startup (missing embedding endpoint, bad Qdrant URL). Check `backend_diagnostics` in `/health`. |
| `holodeck deploy` reinstalled but still missing fields | Stale `uv tool` install. Reinstall: `uv tool install --reinstall --prerelease=allow --python 3.10 --from <repo> --with docker --with exceptiongroup --with 'azure-mgmt-appcontainers>=4.0.0' --with 'azure-identity>=1.15.0' holodeck-ai`. |

## Cleanup

After validation:

```bash
holodeck deploy destroy --force      # tears down the runtime target
```

Don't leave demo deploys running. `--force` skips the confirm prompt — only use it in scripts.

## Authoritative references (always fetch fresh)

- `https://docs.useholodeck.ai/guides/deployment/`
- `https://docs.useholodeck.ai/guides/serve/` (the agent-server runtime that the deployed image runs)
- `https://docs.useholodeck.ai/guides/claude-backend/` (production considerations)
- `https://docs.useholodeck.ai/api/deploy/`
- Anthropic SDK hosting doc: `https://docs.anthropic.com/en/api/agent-sdk/hosting`
