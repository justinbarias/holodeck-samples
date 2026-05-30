import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { CopilotKit } from "@copilotkit/react-core";
import { ThemeProvider } from "@/components/ThemeProvider";
import {
  getServerRuntimeConfig,
  toClientRuntimeConfig,
} from "@/lib/runtime-config";
import { RuntimeConfigProvider } from "@/lib/runtime-config-provider";
import "./globals.css";

export const dynamic = "force-dynamic";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const config = getServerRuntimeConfig();
  return {
    title: config.agentTitle,
    description: config.agentDescription,
  };
}

const COPILOTKIT_ENDPOINT = "/api/copilotkit";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const clientConfig = toClientRuntimeConfig(getServerRuntimeConfig());

  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${jetbrainsMono.variable}`}
    >
      <body className="antialiased">
        <ThemeProvider>
          <RuntimeConfigProvider value={clientConfig}>
            <CopilotKit
              runtimeUrl={COPILOTKIT_ENDPOINT}
              agent={clientConfig.agentId}
            >
              {children}
            </CopilotKit>
          </RuntimeConfigProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
