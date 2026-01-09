import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// CUSTOMIZE: Update title and description for your sample
export const metadata: Metadata = {
  title: "HoloDeck Sample",
  description: "AI-powered assistant",
};

// CUSTOMIZE: Change the agent prop to match your agent name in agent.yaml
// This must match:
// 1. The 'name' field in agent.yaml
// 2. The agent key in route.ts
// 3. The 'agentId' in useAgent hook (page.tsx)
const AGENT_ID = "REPLACE_WITH_AGENT_ID";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <CopilotKit runtimeUrl="/api/copilotkit" agent={AGENT_ID}>
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
