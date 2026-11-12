"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { StandardMarkdown } from "./standard-markdown";

export function DetailsBlock({ title, content }: { title: string; content: string }) {
  return (
    <details className="my-2 rounded-md border border-line-1 bg-surface-secondary px-3 py-2 text-sm">
      <summary className="flex cursor-pointer list-none items-center gap-2 font-medium text-foreground-secondary">
        <ChevronDown size={14} className="transition-transform open:rotate-180" />
        {title}
      </summary>
      <div className="mt-2 border-t border-line-1 pt-2">
        <StandardMarkdown content={content} />
      </div>
    </details>
  );
}
