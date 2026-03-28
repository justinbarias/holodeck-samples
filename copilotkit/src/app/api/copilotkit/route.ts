import { HttpAgent } from "@ag-ui/client";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";

const AGENT_ID = process.env.AGENT_ID ?? "legal_assistant";
const HOLODECK_BACKEND_URL =
  process.env.HOLODECK_BACKEND_URL ?? "http://127.0.0.1:8000/awp";
const COPILOTKIT_ENDPOINT = "/api/copilotkit";

const serviceAdapter = new ExperimentalEmptyAdapter();

const runtime = new CopilotRuntime({
  agents: {
    [AGENT_ID]: new HttpAgent({ url: HOLODECK_BACKEND_URL }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: COPILOTKIT_ENDPOINT,
  });

  return handleRequest(req);
};
