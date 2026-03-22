# HoloDeck CopilotKit Frontend

A generic chat frontend for any [HoloDeck](https://github.com/justinbarias/holodeck) agent. Built with Next.js 16, CopilotKit v2, and the AG-UI protocol.

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Configure your agent (copy and edit)
cp .env.example .env.local

# 3. Start the HoloDeck backend (from the agentlab root)
holodeck serve path/to/agent.yaml

# 4. Start the frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Configuration

All configuration is driven by environment variables. Create a `.env.local` file:

```env
# Required — must match the `name` field in your agent.yaml
NEXT_PUBLIC_AGENT_ID=my_agent

# Required — displayed in the header and browser tab
NEXT_PUBLIC_AGENT_TITLE=My Agent
NEXT_PUBLIC_AGENT_DESCRIPTION=What my agent does

# Optional — defaults shown
NEXT_PUBLIC_HOLODECK_BACKEND_URL=http://127.0.0.1:8000/awp
NEXT_PUBLIC_FILE_ACCEPT=image/*,application/pdf,.doc,.docx,.txt
```

No code changes needed to switch agents.

## Features

- Real-time streaming via AG-UI protocol (SSE)
- Tool call visualization with per-tool-call cards
- Multimodal file uploads (images, PDFs, Office documents)
- Clipboard paste support for images
- Dark/light mode toggle (system preference by default)
- Fully themeable via CSS variables (shadcn/ui compatible)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 16 (App Router) |
| Chat UI | CopilotKit v2 (`@copilotkit/react-core/v2`) |
| Protocol | AG-UI (SSE event stream) |
| Styling | Tailwind CSS v4 + CSS variables |
| Theming | next-themes |
| Language | TypeScript 5 |

## Project Structure

```
src/
├── config.ts                 # All env-driven configuration
├── app/
│   ├── layout.tsx            # Root layout — CopilotKit + ThemeProvider
│   ├── page.tsx              # Chat page — CopilotChat.View (v2 API)
│   ├── globals.css           # Theme variables + component styles
│   └── api/copilotkit/
│       └── route.ts          # API route — proxies to HoloDeck backend
└── components/
    ├── ThemeProvider.tsx      # next-themes wrapper
    ├── ThemeToggle.tsx        # Dark/light mode button
    └── ToolCallRenderer.tsx   # Wildcard tool call renderer (v2 API)
```

## Commands

```bash
npm run dev     # Development server (port 3000)
npm run build   # Production build
npm run lint    # ESLint
```

## How It Works

1. The Next.js API route (`/api/copilotkit`) proxies requests to the HoloDeck backend via `HttpAgent`
2. HoloDeck executes the agent and streams AG-UI events (tool calls, text) back as SSE
3. CopilotKit v2's `CopilotChat.View` renders messages, and `useRenderToolCall` renders tool call cards
4. Each tool invocation gets its own card showing name, arguments, status, and result
