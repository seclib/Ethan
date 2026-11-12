"use client";

import "highlight.js/styles/atom-one-dark-reasonable.css";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { isSafeUrl } from "./safe-url";

export function isSafeHref(href?: string): boolean {
  return isSafeUrl(href);
}

interface StandardMarkdownProps {
  content: string;
  className?: string;
}

/**
 * Rendu Markdown standard pour le flux de lecture.
 *
 * Reste strictement présentationnel : React Markdown échappe le HTML par défaut,
 * les liens sont filtrés par protocole et aucune action privilégiée n'est exposée.
 */
export function StandardMarkdown({ content, className }: StandardMarkdownProps) {
  return (
    <div className={["markdown-body text-sm text-foreground leading-relaxed", className].filter(Boolean).join(" ")}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
          h1: ({ children }) => <h1 className="text-lg font-semibold mt-4 mb-2 tracking-tight">{children}</h1>,
          h2: ({ children }) => <h2 className="text-base font-semibold mt-4 mb-2 tracking-tight">{children}</h2>,
          h3: ({ children }) => <h3 className="text-sm font-semibold mt-3 mb-1">{children}</h3>,
          h4: ({ children }) => <h4 className="text-sm font-medium mt-3 mb-1">{children}</h4>,
          ul: ({ children }) => <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          code: ({ className, children }) => {
            const language = /language-([\w-]+)/.exec(className ?? "")?.[1];
            if (language) {
              return <code className={className} data-language={language}>{children}</code>;
            }
            return <code className="rounded bg-surface-secondary px-1.5 py-0.5 font-mono text-[0.85em] text-accent">{children}</code>;
          },
          pre: ({ children }) => (
            <pre className="my-3 overflow-x-auto rounded-md border border-line-1 bg-bg-1 p-3 font-mono text-xs leading-relaxed">{children}</pre>
          ),
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto rounded-md border border-line-1">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-bg-1">{children}</thead>,
          th: ({ children }) => (
            <th className="border-r border-b border-line-1 px-3 py-1.5 text-left font-semibold last:border-r-0">{children}</th>
          ),
          td: ({ children }) => (
            <td className="border-r border-b border-line-1 px-3 py-1.5 last:border-r-0">{children}</td>
          ),
          a: ({ children, href }) => {
            if (!isSafeUrl(href)) {
              return <span className="text-foreground-tertiary" title="Lien non autorisé">{children}</span>;
            }
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" className="text-accent underline decoration-accent/40 hover:text-accent/80">
                {children}
              </a>
            );
          },
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-line-1 pl-3 text-foreground-secondary italic">{children}</blockquote>
          ),
          hr: () => <hr className="my-4 border-line-1" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
