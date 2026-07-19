# Frontend Components — ETHAN WebUI

> Source of truth for reusable UI components.

## Dashboard

| Component | Path | Purpose |
|-----------|------|---------|
| `DashboardGrid` | `components/dashboard/dashboard-grid.tsx` | Grid + drag/drop + config-driven cards |
| `DashboardCard` | `components/dashboard/dashboard-card.tsx` | Card wrapper around `MetricCard` |
| `MetricCard` | `components/dashboard/metric-card.tsx` | Base card with sparkline + progress |

### CARD_CONFIGS
All dashboard cards are configured in `dashboard-grid.tsx` via `CARD_CONFIGS`.
Adding a new card = adding one entry to this map.

## Charts

| Component | Path | Purpose |
|-----------|------|---------|
| `BarList` | `components/charts/bar-chart.tsx` | Ranked horizontal bar list |
| `StackedBar` | `components/charts/bar-chart.tsx` | Single stacked bar |
| `MiniStats` | `components/charts/bar-chart.tsx` | Compact stats row (label + value) |

## UI Primitives

All in `components/ui/` and exported from `@/components/ui`:
- `button`, `badge`, `input`, `textarea`, `card`
- `dialog`, `dropdown-menu`, `tabs`, `progress`, `skeleton`
- `avatar`, `tooltip`, `command-palette`, `data-table`

## Utilities

- `@/lib/utils` — `cn()` for classnames
- `@/lib/animations.css` — ETHAN keyframes (`ethan-fade-in`, `ethan-pulse`, etc.)

## Design Tokens

See `design/phase-03-design-system/`.