"use client";

import { useCopilotAction } from "@copilotkit/react-core";

interface ToolCallRenderProps {
  name: string;
  args: Record<string, unknown>;
  status: "inProgress" | "complete" | "executing";
}

/**
 * ToolCallRenderer - Renders tool calls from the AG-UI backend
 *
 * Uses useCopilotAction with wildcard pattern to catch all backend tool calls
 * and render them with a consistent UI showing tool name, arguments, and status.
 */
export function ToolCallRenderer() {
  // Wildcard pattern catches all tool calls from the backend
  useCopilotAction({
    name: "*",
    render: ({ name, args, status }: ToolCallRenderProps) => {
      const isInProgress = status === "inProgress";
      const isComplete = status === "complete";

      return (
        <div
          className={`
            my-2 rounded-lg border p-3 text-sm
            ${isInProgress ? "border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-950" : ""}
            ${isComplete ? "border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-950" : ""}
          `}
        >
          {/* Header with tool name and status */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">
              {isInProgress ? "⏳" : isComplete ? "✅" : "🔧"}
            </span>
            <span className="font-semibold text-zinc-800 dark:text-zinc-200">
              {formatToolName(name)}
            </span>
            <span
              className={`
                ml-auto text-xs px-2 py-0.5 rounded-full
                ${isInProgress ? "bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200" : ""}
                ${isComplete ? "bg-green-200 text-green-800 dark:bg-green-800 dark:text-green-200" : ""}
              `}
            >
              {isInProgress ? "Running..." : isComplete ? "Complete" : status}
            </span>
          </div>

          {/* Arguments */}
          {args && Object.keys(args).length > 0 && (
            <div className="mt-2 p-2 rounded bg-zinc-100 dark:bg-zinc-800">
              <div className="text-xs text-zinc-500 dark:text-zinc-400 mb-1">
                Arguments:
              </div>
              <pre className="text-xs overflow-x-auto text-zinc-700 dark:text-zinc-300">
                {JSON.stringify(args, null, 2)}
              </pre>
            </div>
          )}
        </div>
      );
    },
  });

  // This component doesn't render anything itself - it just registers the hook
  return null;
}

/**
 * Format tool name for display
 * Converts snake_case to Title Case with spaces
 */
function formatToolName(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
