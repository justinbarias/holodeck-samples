import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

const serviceAdapter = new ExperimentalEmptyAdapter();

// CUSTOMIZE: Change the agent ID to match your agent name in agent.yaml
// This ID must match:
// 1. The 'name' field in agent.yaml
// 2. The 'agent' prop in CopilotKit provider (layout.tsx)
// 3. The 'agentId' in useAgent hook (page.tsx)
const AGENT_ID = "REPLACE_WITH_AGENT_ID";

const runtime = new CopilotRuntime({
  agents: {
    [AGENT_ID]: new HttpAgent({ url: "http://127.0.0.1:8000/awp" }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
