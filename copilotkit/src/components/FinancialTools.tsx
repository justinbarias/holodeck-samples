"use client";

import { useCallback, useRef, useState } from "react";
import { useAgentContext, useFrontendTool } from "@copilotkit/react-core/v2";
import { z } from "zod";

/**
 * FinancialTools — SPIKE
 *
 * Registers CopilotKit v2 frontend tools (useFrontendTool) that execute in the
 * browser and visibly mutate React state. These tools are sent to the HoloDeck
 * AG-UI backend via `input.tools`, exposed to Claude as dynamic SDK MCP tools
 * (mcp__ag_ui__...), called by Claude, emitted back as AG-UI tool-call events,
 * executed here, and their return value resumes the agent run.
 *
 * Three tools:
 *  - showPortfolioPanel({ ticker? })      → opens a portfolio panel
 *  - requestRiskConfirmation({ action, rationale }) → blocks for approve/reject
 *  - setComparisonTickers({ tickers })    → sets the comparison view
 *
 * The middle tool is the interesting one for the spike: its handler returns a
 * Promise that only resolves once the user clicks a button, so it directly
 * exercises the "halt → frontend executes → resume" round-trip.
 */

type PendingConfirmation = { action: string; rationale: string };

export function FinancialTools() {
  const [portfolioTicker, setPortfolioTicker] = useState<string | null>(null);
  const [comparisonTickers, setComparisonTickers] = useState<string[]>([]);
  const [pending, setPending] = useState<PendingConfirmation | null>(null);
  const [lastDecision, setLastDecision] = useState<string | null>(null);
  const resolveRef = useRef<((decision: string) => void) | null>(null);

  // Frontend-side context nudge so Claude knows these browser tools exist.
  // Sent to the backend over AG-UI as readable context (no HoloDeck change required).
  useAgentContext({
    description: "Available browser UI tools and how to use them",
    value:
      "You can drive the user's browser UI with these frontend tools: " +
      "`showPortfolioPanel` opens a portfolio panel for a ticker; " +
      "`requestRiskConfirmation` asks the user to approve or reject an action and returns their decision; " +
      "`setComparisonTickers` selects tickers to compare side by side. " +
      "Prefer calling these tools to affect the UI rather than only describing actions. " +
      "Always call `requestRiskConfirmation` and wait for the user's approval before comparing or acting on holdings.",
  });

  // 1) showPortfolioPanel({ ticker? })
  useFrontendTool(
    {
      name: "showPortfolioPanel",
      description:
        "Open the portfolio / details panel in the user's UI, optionally focused on a specific stock ticker.",
      parameters: z.object({
        ticker: z
          .string()
          .optional()
          .describe("Stock ticker symbol to focus, e.g. MSFT"),
      }),
      handler: async ({ ticker }) => {
        const symbol = (ticker ?? "").toUpperCase() || null;
        setPortfolioTicker(symbol);
        return symbol
          ? `Portfolio panel opened for ${symbol}.`
          : "Portfolio panel opened.";
      },
      render: ({ status }) => (
        <ToolBadge label="showPortfolioPanel" status={String(status)} />
      ),
    },
    [],
  );

  // 2) requestRiskConfirmation({ action, rationale }) — blocks until user decides
  useFrontendTool(
    {
      name: "requestRiskConfirmation",
      description:
        "Ask the user to approve or reject a potentially risky action. Blocks until the user decides; returns 'approved' or 'rejected'.",
      parameters: z.object({
        action: z
          .string()
          .describe("Short description of the action to confirm"),
        rationale: z.string().describe("Why this action is being proposed"),
      }),
      handler: async ({ action, rationale }) => {
        setPending({ action, rationale });
        const decision = await new Promise<string>((resolve) => {
          resolveRef.current = resolve;
        });
        setPending(null);
        setLastDecision(`${action} → ${decision}`);
        return decision;
      },
      render: ({ status }) => (
        <ToolBadge label="requestRiskConfirmation" status={String(status)} />
      ),
    },
    [],
  );

  // 3) setComparisonTickers({ tickers })
  useFrontendTool(
    {
      name: "setComparisonTickers",
      description:
        "Set the list of stock tickers shown in the UI's comparison view.",
      parameters: z.object({
        tickers: z
          .array(z.string())
          .describe("Tickers to compare, e.g. ['MSFT','NVDA']"),
      }),
      handler: async ({ tickers }) => {
        const upper = tickers.map((t) => t.toUpperCase());
        setComparisonTickers(upper);
        return `Comparison set to: ${upper.join(", ") || "(none)"}`;
      },
      render: ({ status }) => (
        <ToolBadge label="setComparisonTickers" status={String(status)} />
      ),
    },
    [],
  );

  const respond = useCallback((decision: string) => {
    resolveRef.current?.(decision);
    resolveRef.current = null;
  }, []);

  return (
    <aside
      style={{
        width: 320,
        flexShrink: 0,
        borderLeft: "1px solid var(--border, rgba(128,128,128,0.25))",
        padding: "1rem",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        background: "var(--background)",
      }}
      data-testid="financial-tools-panel"
    >
      <h2
        style={{
          fontSize: "0.95rem",
          fontWeight: 600,
          letterSpacing: "-0.01em",
          margin: 0,
        }}
      >
        Frontend Tools (spike)
      </h2>

      {/* Pending risk confirmation — proves halt → resume */}
      {pending ? (
        <section
          data-testid="risk-confirmation"
          style={{
            border: "1px solid var(--hd-tint-border, rgba(123,255,90,0.22))",
            background: "var(--hd-surface-container-high)",
            borderRadius: 10,
            padding: "0.75rem",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            Confirm: {pending.action}
          </div>
          <div style={{ fontSize: "0.8rem", opacity: 0.8, marginBottom: 8 }}>
            {pending.rationale}
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              data-testid="risk-approve"
              onClick={() => respond("approved")}
              style={primaryBtnStyle}
            >
              Approve
            </button>
            <button
              data-testid="risk-reject"
              onClick={() => respond("rejected")}
              style={ghostBtnStyle}
            >
              Reject
            </button>
          </div>
        </section>
      ) : null}

      {/* Portfolio panel */}
      <section data-testid="portfolio-panel">
        <Label>Portfolio panel</Label>
        <div style={cardStyle}>
          {portfolioTicker ? (
            <span style={{ fontWeight: 600, fontSize: "1.1rem" }}>
              {portfolioTicker}
            </span>
          ) : (
            <span style={{ opacity: 0.6 }}>closed</span>
          )}
        </div>
      </section>

      {/* Comparison view */}
      <section data-testid="comparison-view">
        <Label>Comparison</Label>
        <div style={cardStyle}>
          {comparisonTickers.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {comparisonTickers.map((t) => (
                <span
                  key={t}
                  style={{
                    border: "1px solid var(--hd-tint-border, rgba(123,255,90,0.22))",
                    background: "var(--hd-surface-container-high)",
                    borderRadius: 999,
                    padding: "2px 10px",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                  }}
                >
                  {t}
                </span>
              ))}
            </div>
          ) : (
            <span style={{ opacity: 0.6 }}>none selected</span>
          )}
        </div>
      </section>

      {/* Last decision */}
      {lastDecision ? (
        <section data-testid="last-decision">
          <Label>Last decision</Label>
          <div style={cardStyle}>{lastDecision}</div>
        </section>
      ) : null}
    </aside>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: "0.7rem",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        opacity: 0.6,
        marginBottom: 4,
      }}
    >
      {children}
    </div>
  );
}

function ToolBadge({ label, status }: { label: string; status: string }) {
  const done = status?.toLowerCase().includes("complete");
  return (
    <div
      className="holodeck-tool-call"
      style={{ display: "flex", alignItems: "center", gap: 8, fontSize: "0.85rem" }}
    >
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          flexShrink: 0,
          borderRadius: 999,
          background: done ? "var(--hd-primary)" : "var(--hd-primary-soft)",
          boxShadow: done ? "0 0 8px var(--hd-tint-border)" : "none",
        }}
      />
      <span style={{ fontWeight: 600 }}>{label}</span>
      <span style={{ marginLeft: "auto", opacity: 0.7 }}>{status}</span>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid var(--hd-outline, rgba(128,128,128,0.25))",
  borderRadius: 10,
  padding: "0.6rem 0.75rem",
  minHeight: 40,
  display: "flex",
  alignItems: "center",
  background: "var(--hd-surface-container-high)",
};

const primaryBtnStyle: React.CSSProperties = {
  flex: 1,
  background:
    "linear-gradient(90deg, var(--hd-primary-mint), var(--hd-primary-bright))",
  color: "var(--hd-on-primary)",
  border: "none",
  borderRadius: 999,
  padding: "8px 14px",
  fontWeight: 500,
  cursor: "pointer",
};

const ghostBtnStyle: React.CSSProperties = {
  flex: 1,
  background: "var(--hd-surface-container-high)",
  color: "var(--hd-on-surface)",
  border: "1px solid var(--hd-tint-border)",
  borderRadius: 999,
  padding: "8px 14px",
  fontWeight: 500,
  cursor: "pointer",
};
