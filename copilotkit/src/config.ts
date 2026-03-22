/**
 * Shared configuration for the HoloDeck CopilotKit frontend.
 *
 * All values are overridable via NEXT_PUBLIC_* environment variables,
 * making this a generic frontend for any HoloDeck agent.
 *
 * Required env vars (no defaults):
 *   NEXT_PUBLIC_AGENT_ID          — agent name from agent.yaml
 *   NEXT_PUBLIC_AGENT_TITLE       — display title in header / browser tab
 *   NEXT_PUBLIC_AGENT_DESCRIPTION — subtitle / meta description
 *
 * Optional env vars (sensible defaults):
 *   NEXT_PUBLIC_HOLODECK_BACKEND_URL — AWP endpoint (default: http://127.0.0.1:8000/awp)
 *   NEXT_PUBLIC_FILE_ACCEPT          — upload MIME filter
 */

// ---------------------------------------------------------------------------
// Agent
// ---------------------------------------------------------------------------

/** Must match the `name` field in agent.yaml. */
export const AGENT_ID =
  process.env.NEXT_PUBLIC_AGENT_ID ?? "legal_assistant";

// ---------------------------------------------------------------------------
// Backend
// ---------------------------------------------------------------------------

/** HoloDeck serve endpoint (AG-UI / AWP). */
export const HOLODECK_BACKEND_URL =
  process.env.NEXT_PUBLIC_HOLODECK_BACKEND_URL ?? "http://127.0.0.1:8000/awp";

/** CopilotKit API route path (relative to app origin). */
export const COPILOTKIT_ENDPOINT = "/api/copilotkit";

// ---------------------------------------------------------------------------
// UI
// ---------------------------------------------------------------------------

/** Page metadata shown in the browser tab. */
export const PAGE_TITLE =
  process.env.NEXT_PUBLIC_AGENT_TITLE ?? "HoloDeck Assistant";
export const PAGE_DESCRIPTION =
  process.env.NEXT_PUBLIC_AGENT_DESCRIPTION ?? "AI-powered assistant";

/** Header text rendered above the chat widget. */
export const HEADER_TITLE = PAGE_TITLE;
export const HEADER_SUBTITLE = PAGE_DESCRIPTION;

/** MIME types accepted by the file upload input. */
export const FILE_ACCEPT =
  process.env.NEXT_PUBLIC_FILE_ACCEPT ?? "image/*,application/pdf,.doc,.docx,.txt";
