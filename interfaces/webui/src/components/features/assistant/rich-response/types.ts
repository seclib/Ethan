export type CalloutVariant = "info" | "success" | "warning" | "error" | "neutral";

export type ChartKind = "bar" | "line" | "pie";

export type StatusVariant =
  | "success"
  | "warning"
  | "error"
  | "pending"
  | "running"
  | "completed"
  | "disabled"
  | "unknown";

export type DiagramKind = "flow" | "dependency" | "sequence" | "organigram";

export interface CalloutData {
  kind: "callout";
  variant: CalloutVariant;
  title?: string;
  content: string;
}

export interface CodeBlockData {
  kind: "code";
  language: string;
  code: string;
}

export interface ChartData {
  kind: "chart";
  chartType: ChartKind;
  title?: string;
  xKey?: string;
  valueKey?: string;
  data: ChartPoint[];
}

export interface ChartPoint {
  label: string;
  value: number;
  [key: string]: string | number;
}

export interface KpiData {
  kind: "kpi";
  title?: string;
  items: KpiItem[];
}

export interface KpiItem {
  label: string;
  value: string | number;
  trend?: string;
  status?: StatusVariant;
}

export interface StatusData {
  kind: "status";
  status: StatusVariant;
  label?: string;
}

export interface DetailsData {
  kind: "details";
  title: string;
  content: string;
}

export interface DiagramNode {
  id: string;
  label: string;
  x?: number;
  y?: number;
}

export interface DiagramEdge {
  from: string;
  to: string;
  label?: string;
}

export interface DiagramData {
  kind: "diagram";
  diagramType?: DiagramKind;
  title?: string;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
}

export type RichBlock =
  | CalloutData
  | ChartData
  | KpiData
  | StatusData
  | DetailsData
  | DiagramData;

export interface RichSegment {
  id: string;
  type: "markdown" | "code" | "rich";
  value?: string;
  language?: string;
  code?: string;
  block?: RichBlock;
  fallbackCode?: string;
}

const CALLOUT_VARIANTS: CalloutVariant[] = ["info", "success", "warning", "error", "neutral"];
const CHART_KINDS: ChartKind[] = ["bar", "line", "pie"];
const STATUS_VARIANTS: StatusVariant[] = [
  "success",
  "warning",
  "error",
  "pending",
  "running",
  "completed",
  "disabled",
  "unknown",
];
const DIAGRAM_KINDS: DiagramKind[] = ["flow", "dependency", "sequence", "organigram"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown, field: string): string {
  if (typeof value !== "string") throw new Error(`Le champ "${field}" doit être une chaîne.`);
  return value;
}

function optionalString(value: unknown, field: string): string | undefined {
  if (value === undefined || value === null) return undefined;
  return asString(value, field);
}

function asNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new Error(`Le champ "${field}" doit être un nombre.`);
  }
  return value;
}

export function parseJsonStrict(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch (error) {
    const message = error instanceof Error ? error.message : "erreur inconnue";
    throw new Error(`JSON invalide : ${message}`);
  }
}

export function validateCallout(payload: unknown): CalloutData {
  if (!isRecord(payload)) throw new Error("Le bloc callout doit être un objet JSON.");
  const variant = optionalString(payload.variant, "variant") ?? "info";
  if (!CALLOUT_VARIANTS.includes(variant as CalloutVariant)) {
    throw new Error(`Variante de callout inconnue : ${variant}`);
  }
  const content = payload.content === undefined ? "" : asString(payload.content, "content");
  return {
    kind: "callout",
    variant: variant as CalloutVariant,
    title: optionalString(payload.title, "title"),
    content,
  };
}

export function validateChart(payload: unknown): ChartData {
  if (!isRecord(payload)) throw new Error("Le bloc chart doit être un objet JSON.");
  const chartType = optionalString(payload.type, "type") ?? optionalString(payload.chartType, "chartType");
  if (!chartType || !CHART_KINDS.includes(chartType as ChartKind)) {
    throw new Error(`Type de graphique inconnu : ${String(chartType)}`);
  }
  const rawItems = payload.data;
  if (!Array.isArray(rawItems)) throw new Error("Le champ \"data\" doit être un tableau.");
  const data: ChartPoint[] = rawItems.map((item, index) => {
    if (!isRecord(item)) throw new Error(`L'élément ${index} du graphique doit être un objet.`);
    const label = item.label ?? item.name ?? item.x ?? String(index);
    const value = item.value ?? item.y ?? item.count;
    return {
      ...item,
      label: String(label),
      value: asNumber(value, `data[${index}].value`),
    };
  });
  if (data.length === 0) throw new Error("Le graphique doit contenir au moins une donnée.");
  return {
    kind: "chart",
    chartType: chartType as ChartKind,
    title: optionalString(payload.title, "title"),
    xKey: optionalString(payload.xKey, "xKey"),
    valueKey: optionalString(payload.valueKey, "valueKey"),
    data,
  };
}

export function validateKpi(payload: unknown): KpiData {
  if (!isRecord(payload)) throw new Error("Le bloc kpi doit être un objet JSON.");
  const rawItems = payload.items ?? payload.kpis;
  if (!Array.isArray(rawItems) || rawItems.length === 0) {
    throw new Error("Le bloc kpi doit contenir un tableau \"items\" non vide.");
  }
  const items = rawItems.map((item, index) => {
    if (!isRecord(item)) throw new Error(`L'élément ${index} du kpi doit être un objet.`);
    const status = optionalString(item.status, "status");
    if (status !== undefined && !STATUS_VARIANTS.includes(status as StatusVariant)) {
      throw new Error(`Statut unknown : ${status}`);
    }
    return {
      label: asString(item.label ?? item.name, `items[${index}].label`),
      value: (item.value as string | number) ?? "?",
      trend: optionalString(item.trend, "trend"),
      status: status as StatusVariant | undefined,
    };
  });
  return {
    kind: "kpi",
    title: optionalString(payload.title, "title"),
    items,
  };
}

export function validateStatus(payload: unknown): StatusData {
  if (!isRecord(payload)) throw new Error("Le bloc status doit être un objet JSON.");
  const status = asString(payload.status, "status");
  if (!STATUS_VARIANTS.includes(status as StatusVariant)) {
    throw new Error(`Statut inconnu : ${status}`);
  }
  return {
    kind: "status",
    status: status as StatusVariant,
    label: optionalString(payload.label, "label"),
  };
}

export function validateDetails(payload: unknown): DetailsData {
  if (!isRecord(payload)) throw new Error("Le bloc details doit être un objet JSON.");
  return {
    kind: "details",
    title: asString(payload.title ?? "Détails", "title"),
    content: asString(payload.content ?? "", "content"),
  };
}

export function validateDiagram(payload: unknown): DiagramData {
  if (!isRecord(payload)) throw new Error("Le bloc diagram doit être un objet JSON.");
  const nodesRaw = payload.nodes;
  if (!Array.isArray(nodesRaw) || nodesRaw.length === 0) {
    throw new Error("Le diagramme doit contenir des nœuds.");
  }
  const nodes: DiagramNode[] = nodesRaw.map((node, index) => {
    if (!isRecord(node)) throw new Error(`Nœud ${index} invalide.`);
    return {
      id: asString(node.id ?? String(index), "id"),
      label: asString(node.label ?? node.id ?? String(index), "label"),
      x: node.x === undefined ? undefined : asNumber(node.x, "x"),
      y: node.y === undefined ? undefined : asNumber(node.y, "y"),
    };
  });
  const edgesRaw = Array.isArray(payload.edges) ? payload.edges : [];
  const edges: DiagramEdge[] = edgesRaw.map((edge, index) => {
    if (!isRecord(edge)) throw new Error(`Arête ${index} invalide.`);
    return {
      from: asString(edge.from, "from"),
      to: asString(edge.to, "to"),
      label: optionalString(edge.label, "label"),
    };
  });
  const diagramType = optionalString(payload.type, "type");
  if (diagramType !== undefined && !DIAGRAM_KINDS.includes(diagramType as DiagramKind)) {
    throw new Error(`Type de diagramme inconnu : ${diagramType}`);
  }
  return {
    kind: "diagram",
    diagramType: diagramType as DiagramKind | undefined,
    title: optionalString(payload.title, "title"),
    nodes,
    edges,
  };
}

export function validateRichBlock(kind: string, raw: string): RichBlock {
  const payload = parseJsonStrict(raw);
  switch (kind) {
    case "callout":
      return validateCallout(payload);
    case "chart":
      return validateChart(payload);
    case "kpi":
      return validateKpi(payload);
    case "status":
      return validateStatus(payload);
    case "details":
      return validateDetails(payload);
    case "diagram":
    case "flow":
    case "architecture":
      return validateDiagram(payload);
    default:
      throw new Error(`Composant enrichi non reconnu : ${kind}`);
  }
}

export function isRichBlockKind(kind: string): boolean {
  return ["callout", "chart", "kpi", "status", "details", "diagram", "flow", "architecture"].includes(kind);
}
