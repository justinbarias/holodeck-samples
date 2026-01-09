"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import {
  CopilotChat,
  useAgent,
  useCopilotKit,
} from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import { ToolCallRenderer } from "@/components/ToolCallRenderer";
import { randomUUID } from "@copilotkit/shared";

type TextContent = {
  type: "text";
  text: string;
};

type BinaryContent = {
  type: "binary";
  mimeType: string;
  data: string;
  filename?: string;
};

type ContentPart = TextContent | BinaryContent;

type FileUpload = {
  contentType: string;
  bytes: string;
  filename?: string;
};

export default function Page() {
  const [selectedFiles, setSelectedFiles] = useState<FileUpload[]>([]);
  const [inputValue, setInputValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const selectedFilesRef = useRef<FileUpload[]>([]);
  const { copilotkit } = useCopilotKit();
  const { agent } = useAgent({ agentId: "ticket-routing" });

  useEffect(() => {
    selectedFilesRef.current = selectedFiles;
  }, [selectedFiles]);

  const handleFileSelect = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      const filePromises = Array.from(files).map((file) => {
        return new Promise<FileUpload | null>((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64 = (e.target?.result as string)?.split(",")[1];
            if (base64) {
              resolve({
                contentType: file.type,
                bytes: base64,
                filename: file.name,
              });
            } else {
              resolve(null);
            }
          };
          reader.onerror = () => resolve(null);
          reader.readAsDataURL(file);
        });
      });

      const loadedFiles = (await Promise.all(filePromises)).filter(
        (f): f is FileUpload => f !== null
      );
      setSelectedFiles((prev) => [...prev, ...loadedFiles]);

      if (event.target) {
        event.target.value = "";
      }
    },
    []
  );

  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = Array.from(e.clipboardData?.items || []);
      const imageItems = items.filter((item) => item.type.startsWith("image/"));
      if (imageItems.length === 0) return;

      e.preventDefault();

      const imagePromises = imageItems.map((item) => {
        const file = item.getAsFile();
        if (!file) return Promise.resolve(null);

        return new Promise<FileUpload | null>((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => {
            const base64 = (e.target?.result as string)?.split(",")[1];
            if (base64) {
              resolve({
                contentType: file.type,
                bytes: base64,
                filename: `pasted-${Date.now()}.${file.type.split("/")[1]}`,
              });
            } else {
              resolve(null);
            }
          };
          reader.onerror = () => resolve(null);
          reader.readAsDataURL(file);
        });
      });

      const loadedImages = (await Promise.all(imagePromises)).filter(
        (img): img is FileUpload => img !== null
      );
      setSelectedFiles((prev) => [...prev, ...loadedImages]);
    };

    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  }, []);

  const removeFile = useCallback((index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleSubmitMessage = useCallback(
    async (text: string) => {
      if (!agent) {
        console.error("No agent available");
        return;
      }

      const currentFiles = selectedFilesRef.current;
      const hasText = text.trim().length > 0;
      const hasFiles = currentFiles.length > 0;

      if (!hasText && !hasFiles) return;

      let content: string | ContentPart[];

      if (hasFiles) {
        const contentParts: ContentPart[] = [];

        if (hasText) {
          contentParts.push({ type: "text", text: text.trim() });
        }

        for (const file of currentFiles) {
          contentParts.push({
            type: "binary",
            mimeType: file.contentType,
            data: file.bytes,
            filename: file.filename,
          });
        }

        content = contentParts;
      } else {
        content = text.trim();
      }

      setSelectedFiles([]);
      setInputValue("");

      const message = {
        id: randomUUID(),
        role: "user" as const,
        content,
      };

      agent.addMessage(message);
      try {
        await copilotkit.runAgent({ agent });
      } catch (error) {
        console.error("Error running agent:", error);
      }
    },
    [agent, copilotkit]
  );

  const handleStop = useCallback(() => {
    agent?.abortRun?.();
  }, [agent]);

  const messages = agent?.messages ?? [];
  const isRunning = agent?.isRunning ?? false;

  return (
    <div className="flex flex-col h-screen">
      <ToolCallRenderer />

      <header className="border-b border-zinc-200 dark:border-zinc-800 px-6 py-4 bg-white dark:bg-zinc-900">
        <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          HoloDeck Ticket Router
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          AI-Powered Ticket Classification
        </p>
      </header>

      <main className="flex-1 overflow-hidden flex flex-col">
        {selectedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 p-3 border-b border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="relative inline-block w-16 h-16 rounded-lg overflow-hidden border border-zinc-300 dark:border-zinc-600"
              >
                {file.contentType.startsWith("image/") ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`data:${file.contentType};base64,${file.bytes}`}
                    alt={file.filename || `File ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-zinc-200 dark:bg-zinc-700">
                    <span className="text-xs text-zinc-600 dark:text-zinc-300 text-center px-1">
                      {file.filename?.split(".").pop()?.toUpperCase() || "FILE"}
                    </span>
                  </div>
                )}
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-0.5 right-0.5 w-5 h-5 flex items-center justify-center bg-black/60 text-white rounded-full text-xs hover:bg-black/80"
                  aria-label="Remove file"
                >
                  x
                </button>
              </div>
            ))}
          </div>
        )}

        <input
          type="file"
          multiple
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept="image/*,application/pdf,.doc,.docx,.txt"
          className="hidden"
        />

        <CopilotChat.View
          className="flex-1"
          messages={messages}
          isRunning={isRunning}
          inputProps={{
            value: inputValue,
            onChange: setInputValue,
            onSubmitMessage: handleSubmitMessage,
            onStop: handleStop,
            isRunning,
            onAddFile: () => fileInputRef.current?.click(),
          }}
        />
      </main>
    </div>
  );
}
