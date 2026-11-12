"use client";

import * as React from "react";
import { AlertCircle, CheckCircle2, Info, ShieldAlert } from "lucide-react";
import type { CalloutVariant } from "./types";
import { StandardMarkdown } from "./standard-markdown";

const variantStyles: Record<CalloutVariant, { icon: React.ReactNode; border: string; text: string }> = {
  info: {
    icon: <Info size={15} />,
    border: "border-accent/30",
    text: "text-accent",
  },
  success: {
    icon: <CheckCircle2 size={15} />,
    border: "border-green/30",
    text: "text-green",
  },
  warning: {
    icon: <ShieldAlert size={15} />,
    border: "border-gold/40",
    text: "text-gold",
  },
  error: {
    icon: <AlertCircle size={15} />,
    border: "border-red/40",
    text: "text-red",
  },
  neutral: {
    icon: null,
    border: "border-line-1",
    text: "text-foreground-secondary",
  },
};

interface CalloutProps {
  variant: CalloutVariant;
  title?: string;
  content: string;
}

export function Callout({ variant, title, content }: CalloutProps) {
  const style = variantStyles[variant];
  return (
    <div className={`my-2 rounded-md border ${style.border} bg-surface-secondary px-3 py-2 text-sm`}>
      <div className="flex items-start gap-2">
        {style.icon && <span className={`mt-0.5 shrink-0 ${style.text}`}>{style.icon}</span>}
        <div className="min-w-0 flex-1">
          {title && <p className={`mb-1 text-sm font-semibold ${style.text}`}>{title}</p>}
          <StandardMarkdown content={content} className="px-0 py-0" />
        </div>
      </div>
    </div>
  );
}
