"use client";

import { useRenderToolCall } from "@copilotkit/react-core";

interface WildcardRenderProps {
  name: string;
  args: Record<string, unknown>;
  status: "inProgress" | "complete" | "executing";
  result?: unknown;
}

/**
 * ToolCallRenderer - Renders tool calls from the AG-UI backend (v2 API)
 *
 * Uses useRenderToolCall with wildcard "*" to catch all backend tool calls
 * and render them inline in the chat message stream.
 */
export function ToolCallRenderer() {
  useRenderToolCall({
    name: "*",
    render: (props) => {
      const { name, status, result } = props as unknown as WildcardRenderProps;
      const args = (props as unknown as WildcardRenderProps).args as Record<string, unknown> | undefined;
      const isInProgress = status === "inProgress";
      const isComplete = status === "complete";

      return (
        <div className="holodeck-tool-call">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              marginBottom: isComplete && result ? "0.5rem" : 0,
            }}
          >
            <span style={{ fontSize: "1rem" }}>
              {isInProgress ? "\u23F3" : isComplete ? "\u2705" : "\uD83D\uDD27"}
            </span>
            <span style={{ fontWeight: 600 }}>{formatToolName(name)}</span>
            <span
              className={
                isInProgress
                  ? "holodeck-tool-badge holodeck-tool-badge--progress"
                  : "holodeck-tool-badge holodeck-tool-badge--complete"
              }
            >
              {isInProgress ? "Running..." : isComplete ? "Complete" : String(status)}
            </span>
          </div>

          {/* Show arguments (open while in progress, collapsed when complete) */}
          {args && Object.keys(args).length > 0 ? (
            <details className="holodeck-tool-details" open={isInProgress}>
              <summary>Arguments</summary>
              <pre>{JSON.stringify(args, null, 2)}</pre>
            </details>
          ) : null}

          {/* Show result when complete */}
          {isComplete && result ? (
            <details className="holodeck-tool-details">
              <summary>Result</summary>
              <pre>
                {typeof result === "string"
                  ? result
                  : JSON.stringify(result, null, 2)}
              </pre>
            </details>
          ) : null}
        </div>
      );
    },
  });

  return null;
}

/**
 * Format tool name for display.
 * Converts snake_case to Title Case with spaces.
 */
function formatToolName(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
