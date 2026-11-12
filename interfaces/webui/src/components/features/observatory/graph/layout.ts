/**
 * Observatory — simulation de graphe force-directed, sans dépendance.
 *
 * Algorithme classique O(n²) : répulsion Coulomb, attraction par ressorts sur
 * les arêtes, gravité centrale. Déterministe (graine fixe) pour éviter tout
 * tremblement entre deux rendus sur les mêmes données. Bornée à quelques
 * centaines de nœuds (l'endpoint Graph est déjà borné côté Core).
 */

export interface SimNode {
  id: string;
  label: string;
  path: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export interface SimEdge {
  source: string;
  target: string;
}

const ITERATIONS = 160;
const REPULSION = 1400;
const SPRING = 0.045;
const LINK_LENGTH = 90;
const CENTER_GRAVITY = 0.012;
const DAMPING = 0.82;

function pseudoRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 0xffffffff;
  };
}

export function layoutGraph(
  nodes: Array<{ id: string; label: string; path: string }>,
  edges: SimEdge[],
  width: number,
  height: number,
): { nodes: SimNode[]; edges: SimEdge[] } {
  const rand = pseudoRandom(0x5eed);
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 3.2;

  const index = new Map<string, number>();
  const sim: SimNode[] = nodes.map((node, i) => {
    index.set(node.id, i);
    const angle = (i / Math.max(1, nodes.length)) * Math.PI * 2;
    return {
      id: node.id,
      label: node.label,
      path: node.path,
      x: cx + Math.cos(angle) * radius * (0.6 + rand() * 0.4),
      y: cy + Math.sin(angle) * radius * (0.6 + rand() * 0.4),
      vx: 0,
      vy: 0,
    };
  });

  const validEdges = edges
    .map((edge) => [index.get(edge.source), index.get(edge.target)] as const)
    .filter(([a, b]) => a !== undefined && b !== undefined) as Array<readonly [number, number]>;

  for (let iteration = 0; iteration < ITERATIONS; iteration++) {
    const alpha = 1 - iteration / ITERATIONS;

    for (let i = 0; i < sim.length; i++) {
      for (let j = i + 1; j < sim.length; j++) {
        let dx = sim[j].x - sim[i].x;
        let dy = sim[j].y - sim[i].y;
        let distanceSquared = dx * dx + dy * dy;
        if (distanceSquared < 0.01) distanceSquared = 0.01;
        const distance = Math.sqrt(distanceSquared);
        const force = (REPULSION * alpha) / distanceSquared;
        dx /= distance;
        dy /= distance;
        sim[i].vx -= force * dx;
        sim[i].vy -= force * dy;
        sim[j].vx += force * dx;
        sim[j].vy += force * dy;
      }
    }

    for (const [a, b] of validEdges) {
      const dx = sim[b].x - sim[a].x;
      const dy = sim[b].y - sim[a].y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const force = (distance - LINK_LENGTH) * SPRING * alpha;
      const ux = dx / distance;
      const uy = dy / distance;
      sim[a].vx += force * ux;
      sim[a].vy += force * uy;
      sim[b].vx -= force * ux;
      sim[b].vy -= force * uy;
    }

    for (const node of sim) {
      node.vx += (cx - node.x) * CENTER_GRAVITY * alpha;
      node.vy += (cy - node.y) * CENTER_GRAVITY * alpha;
      node.vx *= DAMPING;
      node.vy *= DAMPING;
      node.x += node.vx;
      node.y += node.vy;
    }
  }

  return { nodes: sim, edges };
}
