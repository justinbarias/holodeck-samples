# Financial Assistant — ConvFinQA multi-turn sample (with retrieval)

A HoloDeck sample agent that answers conversational financial questions
grounded in SEC filings, using hybrid (dense + sparse) retrieval over a
multi-company filing archive. It demonstrates an end-to-end Claude
backend with:

- the `hierarchical_document` tool over a PDF corpus,
- native hybrid search through a Qdrant vector store,
- contextual chunking with an Azure OpenAI context model,
- per-turn `numeric` grading and a user-supplied `type: code` grader
  that checks tool-call programs against ConvFinQA's `turn_program`,
- OpenTelemetry traces / metrics / logs exported to a local
  Aspire dashboard.

Each test case is a multi-turn dialogue against a single filing in the
corpus; the agent has to **retrieve** the right chunks via
`convfinqa_archive` and then call the arithmetic tools (`subtract`,
`divide`) to compute the answer.

## Prerequisites

1. **HoloDeck CLI** — from the repo root: `pip install -e .`
2. **Anthropic credentials** — either `ANTHROPIC_API_KEY` or
   `CLAUDE_CODE_OAUTH_TOKEN` (the YAML defaults to
   `model.auth_provider: oauth_token`).
3. **Azure OpenAI** — used for embeddings *and* the contextual-chunk
   model. You need a deployment for an embedding model
   (`text-embedding-3-small` or similar) plus one for a chat model
   (`gpt-4o-mini` works fine). Set
   `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`,
   `AZURE_OPENAI_DEPLOYMENT_NAME`,
   `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`.
4. **Qdrant** — the `convfinqa_archive` tool stores vectors there and
   uses Qdrant's native dense+sparse hybrid search. The fastest way is
   the official Docker image:

   ```bash
   docker run --rm -d --name qdrant \
       -p 6333:6333 -p 6334:6334 \
       -v "$PWD/qdrant_storage:/qdrant/storage" \
       qdrant/qdrant:latest
   ```

   Then set `QDRANT_URL=http://localhost:6333` in `.env`. For Qdrant
   Cloud, use the full URL with `?api_key=…` and put it in
   `QDRANT_REMOTE_URL`.
5. **(Optional) Aspire dashboard** — observability is on by default
   and exports OTLP to `OTEL_EXPORTER_OTLP_ENDPOINT`. To see the
   traces locally:

   ```bash
   docker run --rm -it -p 18888:18888 -p 18889:18889 \
       mcr.microsoft.com/dotnet/aspire-dashboard:latest
   # UI: http://localhost:18888 · OTLP gRPC: localhost:18889
   ```

   Or disable `observability.enabled` in `agent.yaml` if you don't
   want it.

## Run the sample

```bash
cd sample/financial-assistant/claude
cp .env.sample .env             # fill in Anthropic + Azure OpenAI + Qdrant
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest  # if not already running
holodeck test
```

The first run ingests `data/convfinqa-source-5.pdf` into Qdrant
(takes a couple of minutes — pdfminer's bookmark pass is slow on the
3,300-page corpus, hence `execution.file_timeout: 180`). Subsequent
runs reuse the collection.

`agent.yaml` loads its multi-turn test cases from
`data/convfinqa_subset_retrieval.yaml` via the `test_cases_file:`
pointer. Each case asks the agent to find a specific filing in the
archive and compute a derived metric; per-turn reports land under
`results/` (numeric score + per-turn tool assertions + one
`code`-graded turn).

## Regenerate the test subset (optional)

The retrieval-style test cases are generated from the public
ConvFinQA dataset:

```bash
python scripts/convert_convfinqa.py \
    --source <path-to>/convfinqa_dataset.json \
    --split dev --n 10 \
    --retrieval \
    --out data/convfinqa_subset_retrieval.yaml
```

`agent.yaml` already points at the generated file.

## Swap backends (optional)

The hierarchical_document tool's embedding/context choices are tied to
the YAML, but you can flip `model.provider` in `agent.yaml` to
`openai` or `ollama`:

- `openai` — set `OPENAI_API_KEY`; pick any current GPT model name.
- `ollama` — set `OLLAMA_BASE_URL`; pull a tool-capable local model
  (e.g. `llama3.1:70b`).

Note: when `model.provider` is non-Anthropic, the
`embedding_provider:` block in `agent.yaml` is ignored because those
providers ship native embeddings.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ANTHROPIC_API_KEY` / `CLAUDE_CODE_OAUTH_TOKEN` not set | `cp .env.sample .env` and fill in the relevant key for `model.auth_provider` in `agent.yaml` |
| `ConnectionError: ... 6333` | Qdrant isn't running — start the Docker container above, or point `QDRANT_URL` at a remote cluster |
| `AzureOpenAI` 401 / 404 | Verify `AZURE_OPENAI_ENDPOINT`, the API key, and that both the chat *and* embedding deployment names exist in your tenant |
| `ModuleNotFoundError: graders` | Run `holodeck test` from this directory so `agent.yaml`'s parent is on `sys.path` |
| `test_cases_file not found` | Re-run the converter (see above) — the YAML pointer is `data/convfinqa_subset_retrieval.yaml` |
| Ingestion times out on first run | First-time PDF processing is slow; the YAML already widens `execution.file_timeout` to 180s. If still tight, raise it further |
| Grader import error on a mistyped path | `ConfigError` fires at load time — fix the `graders.…:callable` reference |

## Deploying to Azure Container Apps

The `deployment:` block in `agent.yaml` is wired for `holodeck deploy
build` + `holodeck deploy run`. Replace the placeholder
`subscription_id` / `resource_group` / `environment_name` with your
own tenant's values first. The deployed replica defaults to a 2 GiB
ACA container with `session_memory_estimate_mib: 500`, which derives
a safe ceiling of 3 concurrent active turns per replica — see
`docs/guides/claude-backend.md#production-considerations-memory-and-concurrency`
for the math and the tuning knobs.
