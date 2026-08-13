"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownContentProps {
  content: string;
}

/**
 * Rendu markdown des messages assistant, inspiré d'Open-WebUI.
 * - Support GFM (tableaux, listes de tâches, liens, code)
 * - Style cohérent avec le design system ETHAN
 * - Code blocks avec fond sombre et police mono
 */
export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <div className="markdown-body text-sm text-foreground leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Paragraphes
          p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,

          // Titres
          h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
          h2: ({ children }) => <h2 className="text-lg font-bold mt-4 mb-2">{children}</h2>,
          h3: ({ children }) => <h3 className="text-base font-semibold mt-3 mb-1">{children}</h3>,
          h4: ({ children }) => <h4 className="text-sm font-semibold mt-3 mb-1">{children}</h4>,

          // Listes
          ul: ({ children }) => <ul className="list-disc pl-5 my-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 my-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,

          // Code inline
          code: ({ className, children }) => {
            const isBlock = className?.includes("language-");
            if (isBlock) {
              return (
                <code className={className}>{children}</code>
              );
            }
            return (
              <code className="rounded bg-bg-1 px-1.5 py-0.5 font-mono text-[0.85em] text-accent">
                {children}
              </code>
            );
          },

          // Blocs de code
          pre: ({ children }) => (
            <pre className="my-3 overflow-x-auto rounded-lg border border-line-1/20 bg-bg-1 p-3 font-mono text-xs leading-relaxed">
              {children}
            </pre>
          ),

          // Tableaux
          table: ({ children }) => (
            <div className="my-3 overflow-x-auto">
              <table className="w-full border-collapse text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-bg-1/50">{children}</thead>,
          th: ({ children }) => (
            <th className="border border-line-1/20 px-3 py-1.5 text-left font-semibold">{children}</th>
          ),
          td: ({ children }) => (
            <td className="border border-line-1/20 px-3 py-1.5">{children}</td>
          ),

          // Liens
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline hover:text-accent/80"
            >
              {children}
            </a>
          ),

          // Gras / italique
          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,

          // Citations
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-accent/50 pl-3 text-foreground-secondary italic">
              {children}
            </blockquote>
          ),

          // Lignes horizontales
          hr: () => <hr className="my-4 border-line-1/20" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}