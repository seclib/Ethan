"use client";

import * as React from "react";
import { Check, Copy } from "lucide-react";
import { StandardMarkdown } from "./standard-markdown";

interface CodeBlockProps {
  language: string;
  code: string;
}

export function CodeBlock({ language, code }: CodeBlockProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      setCopied(false);
    }
  };

  const content = `\`\`\`${language}\n${code}\n\`\`\``;

  return (
    <div className="my-2 overflow-hidden rounded-md border border-line-1 bg-bg-1">
      <div className="flex items-center justify-between border-b border-line-1 bg-surface-secondary px-3 py-1.5 text-xs">
        <span className="font-mono text-foreground-secondary">{language || "code"}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-foreground-tertiary hover:bg-bg-3 hover:text-foreground"
          aria-label="Copier le code"
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
          <span>{copied ? "Copié" : "Copier"}</span>
        </button>
      </div>
      <StandardMarkdown content={content} className="px-0" />
    </div>
  );
}
