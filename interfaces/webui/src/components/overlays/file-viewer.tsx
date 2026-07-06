"use client";

import { useState } from "react";

interface FileViewerProps {
  open: boolean;
  name?: string;
  content: string;
  language?: string;
  onClose: () => void;
}

const KEYWORDS = /\b(const|let|var|function|return|if|else|for|while|class|import|export|from|async|await|try|catch|throw|new|this|typeof|instanceof)\b/g;
const STRINGS = /(["'`])(?:(?!\1)[^\\]|\\.)*?\1/g;
const COMMENTS = /(\/\/.*$|#.*$|\/\*[\s\S]*?\*\/)/gm;
const NUMBERS = /\b(\d+\.?\d*)\b/g;

function highlightCode(code: string, lang?: string) {
  const escaped = code
    .replace(/&/g, "&")
    .replace(/</g, "<")
    .replace(/>/g, ">");

  const tokens: { type: string; text: string }[] = [];
  let lastIndex = 0;
  const regex = new RegExp(`${COMMENTS.source}|${STRINGS.source}|${KEYWORDS.source}|${NUMBERS.source}`, "g");
  let m: RegExpExecArray | null;

  while ((m = regex.exec(escaped)) !== null) {
    if (m.index > lastIndex) {
      tokens.push({ type: "plain", text: escaped.slice(lastIndex, m.index) });
    }
    if (m[1]) tokens.push({ type: "comment", text: m[0] });
    else if (m[2]) tokens.push({ type: "string", text: m[0] });
    else if (m[3]) tokens.push({ type: "keyword", text: m[0] });
    else if (m[4]) tokens.push({ type: "number", text: m[0] });
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < escaped.length) tokens.push({ type: "plain", text: escaped.slice(lastIndex) });

  return tokens.map((t, i) => {
    if (t.type === "keyword") return <span key={i} className="hl-keyword">{t.text}</span>;
    if (t.type === "string") return <span key={i} className="hl-string">{t.text}</span>;
    if (t.type === "comment") return <span key={i} className="hl-comment">{t.text}</span>;
    if (t.type === "number") return <span key={i} className="hl-number">{t.text}</span>;
    return <span key={i}>{t.text}</span>;
  });
}

export function FileViewer({ open, name = "file.txt", content, language, onClose }: FileViewerProps) {
  const [copied, setCopied] = useState(false);

  if (!open) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="file-viewer-overlay" onClick={onClose}>
      <div className="file-viewer" onClick={(e) => e.stopPropagation()}>
        <div className="file-viewer-header">
          <span className="file-viewer-name">{name}</span>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="file-viewer-close" onClick={handleCopy}>
              {copied ? "Copié" : "Copier"}
            </button>
            <button className="file-viewer-close" onClick={onClose}>✕</button>
          </div>
        </div>
        <div className="file-viewer-body">
          <code>{highlightCode(content, language)}</code>
        </div>
      </div>
    </div>
  );
}