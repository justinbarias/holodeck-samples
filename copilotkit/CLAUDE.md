# CLAUDE.md — HoloDeck CopilotKit Frontend

## What This Is

A Next.js 16 generic frontend for any HoloDeck agent. It uses **CopilotKit v2** (`@copilotkit/react-core/v2`) with the **AG-UI protocol** to communicate with the HoloDeck backend (`holodeck serve`).

## Tech Stack

- **Next.js** 16.1.1 with App Router
- **React** 19.2.3
- **CopilotKit** v1.54.0 (`@copilotkit/react-core`, `@copilotkit/react-ui`, `@copilotkit/runtime`)
- **AG-UI Client** ^0.0.47
- **Tailwind CSS** v4 (CSS-first config via `@import "tailwindcss"` — no `tailwind.config.js`)
- **TypeScript** 5

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout — wraps app in <CopilotKit> provider
│   ├── page.tsx            # Main chat page — uses CopilotChat.View (v2 API)
│   ├── globals.css         # Theme variables + CopilotKit CSS overrides
│   └── api/copilotkit/
│       └── route.ts        # CopilotKit API route (proxies to HoloDeck backend)
├── components/
│   ├── ThemeProvider.tsx    # next-themes wrapper
│   ├── ThemeToggle.tsx      # Dark/light mode toggle button
│   └── ToolCallRenderer.tsx # Wildcard tool call renderer (useCopilotAction)
```

## Key Architecture Decisions

### CopilotKit v2 API
- Uses `CopilotChat.View` (not the v1 `<CopilotChat>` component)
- Imports from `@copilotkit/react-core/v2`
- CSS imported via `@copilotkit/react-core/v2/styles.css` in `page.tsx`
- The v1 CSS (`@copilotkit/react-ui/styles.css`) was **removed** from `layout.tsx` — it conflicts with v2

### CopilotChat.View API (v1.54.0)
The v2 `CopilotChat.View` uses **flat props**, not `inputProps`:
```tsx
<CopilotChat.View
  messages={messages}
  isRunning={isRunning}
  inputValue={inputValue}
  onInputChange={setInputValue}
  onSubmitMessage={handleSubmitMessage}
  onStop={handleStop}
/>
```

### Theming — IMPORTANT
CopilotKit v1.54 uses a **shadcn/ui-style theming system** with CSS variables. The old `--copilot-kit-*` variables (pre-v1.53) no longer work.

CopilotKit's CSS bundles its own **full Tailwind v4 build** which sets theme variables via `@layer theme`. This means:

1. **Tailwind utility classes from the app can conflict** — CopilotKit's bundled Tailwind may override app utilities. Use inline styles or custom CSS classes (e.g. `.holodeck-header`) instead of Tailwind utilities for elements outside the CopilotKit widget.

2. **Theme variables must use `!important`** to override CopilotKit's `@layer theme` defaults. The current approach in `globals.css` sets these on `:root`:
   ```css
   :root {
     --background: #ffffff !important;
     --foreground: #09090b !important;
     --primary: #6366f1 !important;
     /* ... etc */
   }
   ```

3. **Dark mode** uses `html.dark` class selector (controlled by next-themes) to override these same variables with dark values.

### Theme Variables (shadcn/ui style)
These are the variables CopilotKit reads:
```
--background, --foreground
--card, --card-foreground
--popover, --popover-foreground
--primary, --primary-foreground
--secondary, --secondary-foreground
--muted, --muted-foreground
--accent, --accent-foreground
--destructive
--border, --input, --ring
--radius
```

## Commands

```bash
npm run dev     # Start dev server (port 3000)
npm run build   # Production build
npm run lint    # ESLint
```

## Backend Connection

The app connects to HoloDeck via the CopilotKit API route at `/api/copilotkit`. The backend must be running:

```bash
holodeck serve path/to/agent.yaml
```

The agent ID must match across:
1. `agent.yaml` → `name: my_agent`
2. `.env.local` → `NEXT_PUBLIC_AGENT_ID=my_agent`
