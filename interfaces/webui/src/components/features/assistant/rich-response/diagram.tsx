"use client";

import * as React from "react";
import type { DiagramData } from "./types";

const NODE_W = 110;
const NODE_H = 36;

function GraphDiagram({ data }: { data: DiagramData }) {
  const nodes = data.nodes.map((n, i) => {
    if (n.x !== undefined && n.y !== undefined) return n;
    // Auto-layout par colonnes : niveau = position topologique simple.
    const incoming = new Set(data.edges.map((e) => e.to));
    const isRoot = !incoming.has(n.id);
    const column = isRoot ? 0 : 1;
    return {
      ...n,
      x: n.x ?? column * 150 + 20 + (i % 2) * 150,
      y: n.y ?? Math.floor(i / 2) * 60 + 20,
    };
  });

  const maxX = Math.max(...nodes.map((n) => (n.x ?? 0) + NODE_W), 240);
  const maxY = Math.max(...nodes.map((n) => (n.y ?? 0) + NODE_H), 180);

  return (
    <svg viewBox={`0 0 ${maxX + 20} ${maxY + 20}`} className="h-auto w-full" role="img">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <path d="M0,0 L0,6 L9,3 z" fill="#60a5fa" />
        </marker>
      </defs>
      {data.edges.map((edge, i) => {
        const from = nodes.find((n) => n.id === edge.from);
        const to = nodes.find((n) => n.id === edge.to);
        if (!from || !to) return null;
        const x1 = (from.x ?? 0) + NODE_W;
        const y1 = (from.y ?? 0) + NODE_H / 2;
        const x2 = (to.x ?? 0);
        const y2 = (to.y ?? 0) + NODE_H / 2;
        return (
          <g key={`edge-${i}`}>
            <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#60a5fa" strokeWidth={1.2} markerEnd="url(#arrow)" />
            {edge.label && (
              <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 4} textAnchor="middle" fontSize="9" fill="currentColor" className="text-foreground-tertiary">{edge.label}</text>
            )}
          </g>
        );
      })}
      {nodes.map((node) => (
        <g key={node.id}>
          <rect x={node.x} y={node.y} width={NODE_W} height={NODE_H} rx={4} className="fill-surface-elevated stroke-line-1" />
          <text
            x={(node.x ?? 0) + NODE_W / 2}
            y={(node.y ?? 0) + NODE_H / 2 + 3}
            textAnchor="middle"
            fontSize="10"
            fill="currentColor"
            className="text-foreground"
          >
            {node.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

function SequenceDiagram({ data }: { data: DiagramData }) {
  const participants = data.nodes;
  const width = Math.max(260, participants.length * 120);
  const height = 60 + data.edges.length * 28 + 20;
  const participantX = (i: number) => 60 + i * 120;
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img">
      {participants.map((p, i) => (
        <g key={p.id}>
          <rect x={participantX(i) - 45} y={10} width={90} height={24} rx={4} className="fill-surface-elevated stroke-line-1" />
          <text x={participantX(i)} y={26} textAnchor="middle" fontSize="10" fill="currentColor" className="text-foreground">{p.label}</text>
          <line x1={participantX(i)} y1={34} x2={participantX(i)} y2={height - 10} stroke="currentColor" opacity="0.2" />
        </g>
      ))}
      {data.edges.map((edge, i) => {
        const fromIndex = participants.findIndex((p) => p.id === edge.from);
        const toIndex = participants.findIndex((p) => p.id === edge.to);
        if (fromIndex < 0 || toIndex < 0) return null;
        const x1 = participantX(fromIndex);
        const x2 = participantX(toIndex);
        const y = 48 + i * 28;
        const leftToRight = x2 > x1;
        return (
          <g key={`msg-${i}`}>
            <line x1={x1} y1={y} x2={x2} y2={y} stroke="#60a5fa" strokeWidth={1.2} markerEnd="url(#arrow2)" />
            {edge.label && (
              <text x={(x1 + x2) / 2} y={y - 4} textAnchor="middle" fontSize="9" fill="currentColor" className="text-foreground-tertiary">{edge.label}</text>
            )}
          </g>
        );
      })}
      <defs>
        <marker id="arrow2" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <path d="M0,0 L0,6 L9,3 z" fill="#60a5fa" />
        </marker>
      </defs>
    </svg>
  );
}

export function DiagramView({ data }: { data: DiagramData }) {
  return (
    <div className="my-2 rounded-md border border-line-1 bg-surface-secondary px-3 py-2">
      {data.title && <p className="mb-2 text-sm font-semibold text-foreground">{data.title}</p>}
      {data.diagramType === "sequence" ? <SequenceDiagram data={data} /> : <GraphDiagram data={data} />}
    </div>
  );
}
