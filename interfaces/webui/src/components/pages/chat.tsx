"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { formatTime } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Send, Loader2, WifiOff } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  time: string;
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async () => {
    if (!input.trim() || loading || streaming) return;
    const userMsg: Message = {
      role: "user",
      content: input,
      time: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const assistantMsg: Message = {
      role: "assistant",
      content: "",
      time: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const stream = await api.sendMessageStream(userMsg.content);
      setStreaming(true);
      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              const text = parsed.choices?.[0]?.delta?.content || parsed.text || parsed.content || "";
              if (text) {
                setMessages((prev) => {
                  const next = [...prev];
                  next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + text };
                  return next;
                });
              }
            } catch {}
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        if (next.length > 0 && next[next.length - 1].role === "assistant" && !next[next.length - 1].content) {
          next[next.length - 1] = { ...next[next.length - 1], content: "Erreur de communication avec l'API" };
        }
        return next;
      });
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }, [input, loading, streaming]);

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      <div>
        <h1 className="text-2xl font-bold text-text">Chat</h1>
        <p className="text-text-dim text-sm mt-1">Conversation avec ETHAN</p>
      </div>

      <div className="flex-1 overflow-y-auto mt-4 space-y-4 pr-2">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-32 text-text-dim">
            Commencez une conversation avec ETHAN
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === "user"
                  ? "bg-ethan-600 text-white"
                  : "bg-surface-2 border border-border text-text"
              }`}
            >
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || "");
                    if (match) {
                      return (
                        <SyntaxHighlighter
                          style={oneDark}
                          language={match[1]}
                          PreTag="div"
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      );
                    }
                    return (
                      <code className="bg-surface-3 px-1 rounded text-sm" {...props}>
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {msg.content}
              </ReactMarkdown>
              <p className="text-xs text-text-dim mt-1">
                {formatTime(msg.time)}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-text-dim">
            <Loader2 size={16} className="animate-spin" />
            ETHAN réfléchit...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Message ETHAN..."
          disabled={loading || streaming}
          className="flex-1 rounded-lg border border-border bg-surface-2 px-4 py-2 text-text placeholder-text-dim focus:outline-none focus:border-ethan-500 disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={loading || streaming || !input.trim()}
          className="rounded-lg bg-ethan-600 px-4 py-2 text-white hover:bg-ethan-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {streaming ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </button>
      </div>
    </div>
  );
}