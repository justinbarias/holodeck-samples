/**
 * Runtime configuration for the HoloDeck CopilotKit frontend.
 *
 * All values are driven by environment variables at runtime (no NEXT_PUBLIC_ prefix).
 * Server Components read process.env directly; client components read from
 * window.__RUNTIME_CONFIG__ which is injected by layout.tsx via a <script> tag.
 */

export type RuntimeConfig = {
  agentId: string;
  agentTitle: string;
  agentDescription: string;
  fileAccept: string;
};

/** Server-side: read process.env at request time. */
export function getServerRuntimeConfig(): RuntimeConfig {
  return {
    agentId: process.env.AGENT_ID ?? "legal_assistant",
    agentTitle: process.env.AGENT_TITLE ?? "HoloDeck Assistant",
    agentDescription:
      process.env.AGENT_DESCRIPTION ?? "AI-powered assistant",
    fileAccept:
      process.env.FILE_ACCEPT ?? "image/*,application/pdf,.doc,.docx,.txt",
  };
}

/** Client-side: read from injected window global. */
export function getClientRuntimeConfig(): RuntimeConfig {
  if (typeof window !== "undefined" && window.__RUNTIME_CONFIG__) {
    return window.__RUNTIME_CONFIG__;
  }
  return { agentId: "", agentTitle: "", agentDescription: "", fileAccept: "" };
}

declare global {
  interface Window {
    __RUNTIME_CONFIG__?: RuntimeConfig;
  }
}
