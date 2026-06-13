# Financial Assistant — ConvFinQA multi-turn sample (OpenAI backend)

A HoloDeck sample agent that answers conversational financial questions
grounded in SEC filings, using hybrid (dense + sparse) retrieval over a
multi-company filing archive. This is the **OpenAI Agents backend**
variant (`model.provider: azure_openai`); see [`../claude`](../claude)
for the Anthropic version. It demonstrates:

- the `hierarchical_document` tool over a PDF corpus,
- native hybrid search through a Qdrant vector store,
- contextual chunking with an Azure OpenAI context model,
- **native structured output** — the SDK enforces a JSON schema on every
  final response, so the prompt doesn't have to police format,
- **reasoning effort** (`openai.effort: high`) so a reasoning model can
  derive a ratio from a sensitivity disclosure on turn 2,
- per-turn `numeric` grading against ConvFinQA ground truth,
- OpenTelemetry traces / metrics / logs exported to a local
  Aspire dashboard.

Each test case is a multi-turn dialogue against a single filing in the
corpus; the agent has to **retrieve** the right chunks via
`convfinqa_archive` and then call the arithmetic tools (`subtract`,
`divide`) to compute the answer.

## Prerequisites

1. **HoloDeck CLI with the OpenAI extra** — the OpenAI Agents backend is
   an optional extra (the SDK is imported only when this backend runs):

   ```bash
   uv tool install "holodeck-ai[openai-agents,qdrant]@latest" \
       --prerelease allow --python 3.10
   ```

   (From a source checkout: `pip install -e '.[openai-agents,qdrant]'`.)
2. **Azure OpenAI** — used for the chat model, embeddings, *and* the
   contextual-chunk model. You need a deployment for a chat model and
   one for an embedding model (`text-embedding-3-small` or similar). Set
   `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`,
   `AZURE_OPENAI_DEPLOYMENT_NAME`,
   `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`.

   > Prefer plain OpenAI? Flip `model.provider` to `openai`, set
   > `model.name` to a model id (e.g. `gpt-4o`), drop the `endpoint`,
   > and set `OPENAI_API_KEY`. See [Swap providers](#swap-providers-optional).
3. **Qdrant** — the `convfinqa_archive` tool stores vectors there and
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
4. **(Optional) Aspire dashboard** — observability is on by default
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
cd financial-assistant/openai
cp .env.sample .env             # fill in Azure OpenAI + Qdrant
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
`results/` (numeric score + per-turn tool assertions).

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

## Swap providers (optional)

The agent is wired for `azure_openai`. To run against plain OpenAI,
edit `model:` in `agent.yaml`:

```yaml
model:
  provider: openai
  name: gpt-4o          # or any current model id
  api_key: ${OPENAI_API_KEY}
  temperature: 0.0
```

Set `OPENAI_API_KEY` in `.env`. When `model.provider` is `openai`,
the provider ships native embeddings, so you can also point the
`embedding_provider:` and `context_model:` blocks at `openai` instead
of `azure_openai` (or leave them on Azure if that's where your
embedding deployment lives).

For the Anthropic / Ollama version, use the sibling
[`../claude`](../claude) sample instead — those providers route through
the Claude backend.

## Structured output note

OpenAI's structured-output mode rejects JSON-Schema `oneOf`; the
supported spelling is `anyOf`. The `response_format` block in
`agent.yaml` uses `anyOf` for the `answer` field (a number **or** a
`NaN`/percent string). The same schema on the Claude backend accepts
`oneOf` — this is the one portability wrinkle between the two variants.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: agents` / missing-dependency error at startup | Install the OpenAI extra: `pip install -e '.[openai-agents]'` (or the `uv tool install` line above) |
| `AzureOpenAI` 401 / 404 | Verify `AZURE_OPENAI_ENDPOINT`, the API key, and that the chat *and* embedding deployment names exist in your tenant |
| `Invalid schema for response_format: 'oneOf' is not permitted` | Use `anyOf` in `response_format` — OpenAI doesn't accept `oneOf` (see note above) |
| `ConnectionError: ... 6333` | Qdrant isn't running — start the Docker container above, or point `QDRANT_URL` at a remote cluster |
| `ModuleNotFoundError: graders` | Run `holodeck test` from this directory so `agent.yaml`'s parent is on `sys.path` |
| `test_cases_file not found` | Re-run the converter (see above) — the YAML pointer is `data/convfinqa_subset_retrieval.yaml` |
| Ingestion times out on first run | First-time PDF processing is slow; the YAML already widens `execution.file_timeout` to 180s. If still tight, raise it further |

## Serving & deploying

`holodeck serve` and `holodeck deploy` are **not yet supported on the
OpenAI Agents backend** — they are on the roadmap. The `deployment:`
block is included in `agent.yaml` for parity with the Claude variant,
but today this sample is exercised via `holodeck test` / `holodeck chat`.
If you need a deployable agent now, use the
[`../claude`](../claude) variant, where serve/deploy are fully wired.
