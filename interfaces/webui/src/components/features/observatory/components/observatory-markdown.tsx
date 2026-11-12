"use client";

/**
 * Observatory — rendu Markdown avec support des wikiliens [[document]].
 *
 * Les wikiliens sont réécrits en liens internes `observatory-wikilink:<nom>` :
 * le composant de lien ci-dessous les intercepte, résout la cible via le Core
 * (GET /v1/memory/vault/resolve) et appelle `onNavigate` avec le chemin
 * résolu. Aucun wikilien n'est deviné côté client : la résolution est
 * serveur-side, exacte et testable.
 */

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { rewriteWikilinks } from "./wikilinks";

// La logique pure de réécriture est importable pour les tests : voir ./wikilinks.
export { rewriteWikilinks };

interface ObservatoryMarkdownProps {
	content: string;
	onWikilink: (wikilink: string) => void;
	className?: string;
}

export function ObservatoryMarkdown({ content, onWikilink, className }: ObservatoryMarkdownProps) {
	const rendered = React.useMemo(() => rewriteWikilinks(content), [content]);

	return (
		<div className={cn("observatory-markdown text-[13px] leading-relaxed text-foreground", className)}>
			<ReactMarkdown
				remarkPlugins={[remarkGfm]}
				components={{
					h1: ({ children }) => <h1 className="mt-3 mb-2 text-xl font-bold tracking-tight">{children}</h1>,
					h2: ({ children }) => <h2 className="mt-3 mb-2 text-lg font-semibold tracking-tight">{children}</h2>,
					h3: ({ children }) => <h3 className="mt-2 mb-1.5 text-base font-semibold">{children}</h3>,
					h4: ({ children }) => <h4 className="mt-2 mb-1 text-sm font-semibold">{children}</h4>,
					p: ({ children }) => <p className="my-2">{children}</p>,
					ul: ({ children }) => <ul className="my-2 list-disc pl-5 space-y-1">{children}</ul>,
					ol: ({ children }) => <ol className="my-2 list-decimal pl-5 space-y-1">{children}</ol>,
					li: ({ children }) => <li>{children}</li>,
					code: ({ className: codeClass, children }) =>
						codeClass?.includes("language-") ? (
							<code className={codeClass}>{children}</code>
						) : (
							<code className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-[0.85em] text-primary">{children}</code>
						),
					pre: ({ children }) => (
						<pre className="my-2 overflow-x-auto rounded-lg border border-line-1 bg-bg-2 p-3 font-mono text-xs leading-relaxed">{children}</pre>
					),
					blockquote: ({ children }) => (
						<blockquote className="my-2 border-l-2 border-primary/50 pl-3 italic text-foreground-secondary">{children}</blockquote>
					),
					table: ({ children }) => (
						<div className="my-2 overflow-x-auto">
							<table className="w-full border-collapse text-xs">{children}</table>
						</div>
					),
					th: ({ children }) => <th className="border border-line-1 bg-bg-2 px-2 py-1 text-left font-semibold">{children}</th>,
					td: ({ children }) => <td className="border border-line-1 px-2 py-1">{children}</td>,
					hr: () => <hr className="my-4 border-line-1" />,
					a: ({ children, href }) => {
						if (href?.startsWith("observatory-wikilink:")) {
							const raw = decodeURIComponent(href.slice("observatory-wikilink:".length));
							return (
								<button
									type="button"
									className="text-primary underline underline-offset-2 hover:text-primary/80"
									onClick={() => onWikilink(raw)}
								>
									{children}
								</button>
							);
						}
						return (
							<a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline hover:text-primary/80">
								{children}
							</a>
						);
					},
				}}
			>
				{rendered}
			</ReactMarkdown>
		</div>
	);
}
