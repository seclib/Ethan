"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Send, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function AssistantPage() {
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hi! How can I help?",
      timestamp: new Date(),
    },
    {
      id: "2",
      role: "user",
      content: "Deploy my app",
      timestamp: new Date(),
    },
    {
      id: "3",
      role: "assistant",
      content: "I'll help you deploy. Here's the plan:\n1. Build Docker image\n2. Push to registry\n3. Deploy to Kubernetes\nShould I proceed?",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content }),
      });

      const data = await res.json();
      if (data.reply) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: data.reply,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in flex flex-col h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Assistant Chat</h1>
          <p className="text-muted-foreground mt-1">Chat directly with the ETHAN cognitive core</p>
        </div>
        <Button className="gap-2">
          <Plus size={16} /> New
        </Button>
      </div>

      <Card variant="outlined" className="flex-1 flex flex-col overflow-hidden min-h-[500px]">
        <CardHeader className="border-b bg-card/50 pb-4">
          <div className="flex items-center gap-2">
            <CardTitle>Messages</CardTitle>
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse ml-2" />
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-0 flex flex-col bg-muted/10">
          <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-4",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                {message.role === "assistant" && (
                  <Avatar fallback="ETH" size="md" className="bg-accent/20 text-accent font-semibold flex-shrink-0" />
                )}
                <div
                  className={cn(
                    "max-w-[80%] rounded-2xl px-5 py-3 shadow-sm",
                    message.role === "user"
                      ? "bg-accent text-accent-foreground rounded-tr-sm"
                      : "bg-card text-foreground border rounded-tl-sm"
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                </div>
                {message.role === "user" && (
                  <Avatar fallback="YOU" size="md" className="bg-secondary text-secondary-foreground font-semibold flex-shrink-0" />
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4 justify-start">
                <Avatar fallback="ETH" size="md" className="bg-accent/20 text-accent font-semibold flex-shrink-0" />
                <div className="bg-card border rounded-2xl rounded-tl-sm px-5 py-3 shadow-sm flex items-center gap-1">
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce" />
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce delay-75" />
                  <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full animate-bounce delay-150" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="p-4 bg-card border-t">
            <div className="flex gap-3 max-w-4xl mx-auto">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend())}
                placeholder="Type a message..."
                disabled={isLoading}
                className="flex-1 rounded-full px-6 bg-muted/50 border-transparent focus-visible:bg-background focus-visible:ring-accent"
              />
              <Button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="rounded-full w-10 h-10 p-0 flex items-center justify-center shrink-0"
              >
                <Send className="w-4 h-4 ml-0.5" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}