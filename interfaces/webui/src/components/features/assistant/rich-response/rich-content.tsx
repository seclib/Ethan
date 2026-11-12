"use client";

import * as React from "react";
import type { RichBlock, RichSegment } from "./types";
import { parseRichContent } from "./parse-rich-content";
import { StandardMarkdown } from "./standard-markdown";
import { CodeBlock } from "./code-block";
import { Callout } from "./callout";
import { ChartView } from "./chart";
import { KpiGrid } from "./kpi";
import { StatusBadge } from "./status-badge";
import { DetailsBlock } from "./details";
import { DiagramView } from "./diagram";

class RichErrorBoundary extends React.Component<{ fallback: React.ReactNode; children: React.ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

function RenderRichBlock({ block }: { block: RichBlock }) {
  switch (block.kind) {
    case "callout":
      return <Callout variant={block.variant} title={block.title} content={block.content} />;
    case "chart":
      return <ChartView data={block} />;
    case "kpi":
      return <KpiGrid data={block} />;
    case "status":
      return <StatusBadge status={block.status} label={block.label ?? block.status} />;
    case "details":
      return <DetailsBlock title={block.title} content={block.content} />;
    case "diagram":
      return <DiagramView data={block} />;
    default:
      return (
        <CodeBlock language="json" code={JSON.stringify(block, null, 2)} />
      );
  }
}

export interface RichContentProps {
  content: string;
  className?: string;
}

export function RichContent({ content, className }: RichContentProps) {
  const segments = React.useMemo(() => parseRichContent(content), [content]);

  return (
    <div className={className ?? "ethan-response-renderer text-sm leading-relaxed"}>
      {segments.map((segment: RichSegment) => {
        if (segment.type === "markdown") {
          return <StandardMarkdown key={segment.id} content={segment.value ?? ""} />;
        }
        if (segment.type === "code") {
          return <CodeBlock key={segment.id} language={segment.language ?? "text"} code={segment.code ?? ""} />;
        }
        if (segment.type === "rich" && segment.block) {
          return (
            <RichErrorBoundary key={segment.id} fallback={<CodeBlock language="text" code={segment.fallbackCode ?? ""} />}>
              <RenderRichBlock block={segment.block} />
            </RichErrorBoundary>
          );
        }
        return null;
      })}
    </div>
  );
}

export default RichContent;
