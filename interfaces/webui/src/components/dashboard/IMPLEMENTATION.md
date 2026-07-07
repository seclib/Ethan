# Dashboard Vivant — Implémentation avancée

## 1. Connexion aux endpoints API réels

### 1.1 Architecture

```
DashboardGrid
  └── useLiveMetric<T>(endpoint, interval)
        ├── EventSource (SSE)
        ├── Fallback polling
        └── Retry exponentiel
```

### 1.2 Endpoints API

| Carte | Endpoint SSE | Endpoint REST | Fréquence |
|-------|--------------|---------------|-----------|
| Core | `/api/metrics/core/stream` | `/api/metrics/core` | 5s |
| CPU | `/api/metrics/cpu/stream` | `/api/metrics/cpu` | 1s |
| RAM | `/api/metrics/ram/stream` | `/api/metrics/ram` | 2s |
| GPU | `/api/metrics/gpu/stream` | `/api/metrics/gpu` | 2s |
| Providers | `/api/metrics/providers/stream` | `/api/metrics/providers` | 5s |
| Tokens | `/api/metrics/tokens/stream` | `/api/metrics/tokens` | 1s |
| Agents | `/api/metrics/agents/stream` | `/api/metrics/agents` | 3s |
| Planner | `/api/metrics/planner/stream` | `/api/metrics/planner` | 2s |
| Knowledge | `/api/metrics/knowledge/stream` | `/api/metrics/knowledge` | 5s |
| Memory | `/api/metrics/memory/stream` | `/api/metrics/memory` | 3s |
| MCP | `/api/metrics/mcp/stream` | `/api/metrics/mcp` | 5s |
| Plugins | `/api/metrics/plugins/stream` | `/api/metrics/plugins` | 10s |
| Events | `/api/metrics/events/stream` | `/api/metrics/events` | 1s |
| Network | `/api/metrics/network/stream` | `/api/metrics/network` | 2s |

### 1.3 Format SSE

```
event: metric
data: {"timestamp": 1699123456789, "value": {"usage": 42, "cores": 8}}
```

### 1.4 Implémentation

```typescript
// hooks/useLiveMetric.ts
export function useLiveMetric<T>(
  endpoint: string,
  interval: number = 1000
): { data: T | null; error: Error | null; loading: boolean } {
  // ... existing code ...
  
  const connect = () => {
    const eventSource = new EventSource(endpoint);
    
    eventSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data) as { timestamp: number; value: T };
      setData(parsed.value);
    };
    
    eventSource.onerror = () => {
      // Fallback to polling
      setError(new Error("SSE failed, falling back to polling"));
      startPolling(endpoint.replace('/stream', ''));
    };
  };
  
  return { data, error, loading };
}
```

## 2. Drill-down par carte

### 2.1 Navigation

Chaque carte est cliquable et navigue vers la page détaillée :

| Carte | Page cible | Paramètres |
|-------|-----------|------------|
| Core | `/system` | - |
| CPU | `/system?tab=cpu` | - |
| RAM | `/system?tab=ram` | - |
| GPU | `/system?tab=gpu` | - |
| Providers | `/providers` | - |
| Tokens | `/assistant?tab=tokens` | - |
| Agents | `/agents` | - |
| Planner | `/planner` | - |
| Knowledge | `/knowledge` | - |
| Memory | `/memory` | - |
| MCP | `/tools` | - |
| Plugins | `/plugins` | - |
| Events | `/logs` | filter=events |
| Network | `/system?tab=network` | - |

### 2.2 Implémentation

```typescript
// components/dashboard/metric-card.tsx
interface MetricCardProps {
  // ... existing props
  href?: string;  // NEW
  onClick?: () => void;
}

export function MetricCard({ ..., href, onClick }: MetricCardProps) {
  const handleClick = () => {
    if (href) {
      router.push(href);
    } else if (onClick) {
      onClick();
    }
  };

  return (
    <div
      className="..."
      onClick={handleClick}
      role={href ? "link" : "button"}
      tabIndex={0}
    >
      {/* ... */}
    </div>
  );
}
```

### 2.3 Usage

```typescript
// cards/cpu-card.tsx
<MetricCard
  title="CPU"
  value={`${data.usage}%`}
  status={getStatus(data.usage)}
  icon="⚡"
  href="/system?tab=cpu"  // NEW
  onClick={() => {}}
/>
```

## 3. Drag & Drop

### 3.1 Bibliothèque

Utiliser `@dnd-kit/core` + `@dnd-kit/sortable` :

```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

### 3.2 Architecture

```typescript
// components/dashboard/dashboard-grid.tsx
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, arrayMove, verticalListSortingStrategy } from '@dnd-kit/sortable';

export function DashboardGrid() {
  const [cards, setCards] = useState<string[]>(['core', 'cpu', 'ram', 'gpu', ...]);
  
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setCards(arrayMove(cards, cards.indexOf(active.id), cards.indexOf(over.id)));
    }
  };
  
  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={cards} strategy={verticalListSortingStrategy}>
        {cards.map((cardId) => (
          <SortableCard key={cardId} id={cardId} />
        ))}
      </SortableContext>
    </DndContext>
  );
}
```

### 3.3 Persistance

```typescript
// hooks/useDashboardLayout.ts
export function useDashboardLayout() {
  const [layout, setLayout] = useState<string[]>([]);
  
  useEffect(() => {
    const saved = localStorage.getItem('dashboard-layout');
    if (saved) {
      setLayout(JSON.parse(saved));
    }
  }, []);
  
  const updateLayout = (newLayout: string[]) => {
    setLayout(newLayout);
    localStorage.setItem('dashboard-layout', JSON.stringify(newLayout));
  };
  
  return { layout, updateLayout };
}
```

## 4. Sparklines historiques

### 4.1 Bibliothèque

Utiliser `recharts` :

```bash
npm install recharts
```

### 4.2 Hook de historique

```typescript
// hooks/useMetricHistory.ts
export function useMetricHistory<T>(
  endpoint: string,
  maxPoints: number = 30
): { data: T[]; timestamps: number[] } {
  const [data, setData] = useState<T[]>([]);
  const [timestamps, setTimestamps] = useState<number[]>([]);
  
  useEffect(() => {
    const eventSource = new EventSource(endpoint);
    
    eventSource.onmessage = (event) => {
      const parsed = JSON.parse(event.data) as { timestamp: number; value: T };
      
      setData(prev => [...prev.slice(-maxPoints + 1), parsed.value]);
      setTimestamps(prev => [...prev.slice(-maxPoints + 1), parsed.timestamp]);
    };
    
    return () => eventSource.close();
  }, [endpoint, maxPoints]);
  
  return { data, timestamps };
}
```

### 4.3 Composant Sparkline

```typescript
// components/widgets/sparkline.tsx
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SparklineProps {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export function Sparkline({ data, color = '#3b82f6', width = 100, height = 32 }: SparklineProps) {
  const chartData = data.map((value, index) => ({ index, value }));
  
  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          animationDuration={300}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 4.4 Intégration dans MetricCard

```typescript
// components/dashboard/metric-card.tsx
import { Sparkline } from '@/components/widgets/sparkline';

interface MetricCardProps {
  // ... existing props
  sparkline?: number[];  // Already exists!
}

export function MetricCard({ ..., sparkline }: MetricCardProps) {
  return (
    <div className="...">
      {/* ... existing content ... */}
      
      {sparkline && sparkline.length > 1 && (
        <div className="mt-3 h-8">
          <Sparkline data={sparkline} />
        </div>
      )}
    </div>
  );
}
```

### 4.5 Usage dans les cartes

```typescript
// cards/cpu-card.tsx
export function CpuCard({ data, loading }: CpuCardProps) {
  const { data: history } = useMetricHistory<number>('/api/metrics/cpu/stream');
  
  return (
    <MetricCard
      title="CPU"
      value={`${data?.usage}%`}
      status={getStatus(data?.usage ?? 0)}
      icon="⚡"
      sparkline={history}  // NEW
      href="/system?tab=cpu"
    />
  );
}
```

## 5. Intégration complète

### 5.1 Mise à jour de DashboardGrid

```typescript
// components/dashboard/dashboard-grid.tsx
import { useDashboardLayout } from '@/hooks/useDashboardLayout';
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, arrayMove, verticalListSortingStrategy } from '@dnd-kit/sortable';

export function DashboardGrid() {
  const { layout, updateLayout } = useDashboardLayout();
  const [cards, setCards] = useState<string[]>(layout);
  
  // Sync layout changes
  useEffect(() => {
    updateLayout(cards);
  }, [cards]);
  
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setCards(arrayMove(cards, cards.indexOf(active.id as string), cards.indexOf(over.id as string)));
    }
  };
  
  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={cards} strategy={verticalListSortingStrategy}>
        <div className="db-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
          {cards.map((cardId) => (
            <SortableCard key={cardId} id={cardId} cardType={cardId} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}
```

### 5.2 Ordre par défaut

```typescript
const DEFAULT_LAYOUT = [
  'core',
  'cpu',
  'ram',
  'gpu',
  'providers',
  'tokens',
  'agents',
  'planner',
  'knowledge',
  'memory',
  'mcp',
  'plugins',
  'events',
  'network',
];
```

## 6. Tests

### 6.1 Tests unitaires

```typescript
// tests/unit/dashboard/cards.test.ts
describe('CpuCard', () => {
  it('should display loading state', () => {
    render(<CpuCard data={null} loading={true} />);
    expect(screen.getByText('—')).toBeDefined();
  });
  
  it('should display CPU usage', () => {
    render(<CpuCard data={{ usage: 42, ... }} loading={false} />);
    expect(screen.getByText('42%')).toBeDefined();
  });
  
  it('should show critical status when usage > 80%', () => {
    render(<CpuCard data={{ usage: 85, ... }} loading={false} />);
    expect(screen.getByText('85%').closest('[data-status="critical"]')).toBeDefined();
  });
});
```

### 6.2 Tests E2E

```typescript
// tests/e2e/dashboard.spec.ts
test('dashboard loads with 14 cards', async ({ page }) => {
  await page.goto('/');
  await page.waitForSelector('[data-testid="metric-card"]');
  const cards = await page.locator('[data-testid="metric-card"]').count();
  expect(cards).toBe(14);
});

test('cards are draggable', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('[data-testid="metric-card"]').first();
  const secondCard = page.locator('[data-testid="metric-card"]').nth(1);
  
  await firstCard.dragTo(secondCard);
  await expect(firstCard).toHaveAttribute('data-order', '1');
});
```

## 7. Performance

### 7.1 Optimisations

- **Memoization** : `React.memo` sur chaque carte
- **Debounce** : mise à jour UI throttlée à 30 FPS max
- **Virtualisation** : si > 20 cartes (react-window)
- **Lazy loading** : cartes chargées à la demande

### 7.2 Limites

- Max 14 cartes affichées simultanément
- Fallback polling si SSE échoue (> 3s sans donnée)
- Cache local : dernière valeur connue affichée

## 8. Checklist d'implémentation

- [ ] Créer les endpoints API SSE (`/api/metrics/*/stream`)
- [ ] Créer les endpoints REST (`/api/metrics/*`)
- [ ] Connecter les cartes aux endpoints réels
- [ ] Ajouter `href` à chaque carte pour drill-down
- [ ] Installer `@dnd-kit/core` + `@dnd-kit/sortable`
- [ ] Implémenter `DndContext` dans `DashboardGrid`
- [ ] Créer hook `useDashboardLayout` avec localStorage
- [ ] Installer `recharts`
- [ ] Créer composant `Sparkline`
- [ ] Ajouter `useMetricHistory` hook
- [ ] Connecter sparklines aux cartes
- [ ] Écrire tests unitaires
- [ ] Écrire tests E2E
- [ ] Vérifier performance (Lighthouse > 90)