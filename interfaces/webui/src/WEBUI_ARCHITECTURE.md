# ETHAN WebUI — Architecture Documentation

## Overview

ETHAN WebUI is a modern, maintainable, and scalable web interface for the ETHAN Cognitive Runtime. Built with Next.js 15, React 19, TypeScript 5, and Tailwind CSS 4.

## Architecture Principles

1. **Separation of Concerns** — UI, logic, and data layers are strictly separated
2. **Type Safety** — Full TypeScript coverage with strict mode
3. **Modularity** — Feature-based organization for easy scaling
4. **Performance** — Lazy loading, code splitting, and optimized re-renders
5. **Accessibility** — Keyboard navigation, reduced motion support, ARIA labels
6. **Maintainability** — Clear conventions, comprehensive documentation, tests

## Project Structure

```
interfaces/webui/src/
├── app/                          # Next.js App Router
│   ├── layout.tsx                # Root layout (providers)
│   ├── page.tsx                  # Landing page
│   ├── globals.css               # Global styles
│   ├── (auth)/                   # Auth routes (future)
│   └── (dashboard)/              # Dashboard routes
│       ├── layout.tsx            # Dashboard layout
│       ├── page.tsx              # Dashboard home
│       ├── agents/               # Agents pages
│       ├── goals/                # Goals pages
│       ├── memory/               # Memory pages
│       ├── skills/               # Skills pages
│       ├── flux/                 # Event flux
│       └── settings/             # Settings pages
│
├── components/
│   ├── ui/                       # Reusable UI components (shadcn-style)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   ├── layouts/                  # Layout components
│   │   ├── sidebar.tsx
│   │   ├── topbar.tsx
│   │   └── inspector.tsx
│   ├── features/                 # Feature-specific components
│   │   ├── agents/
│   │   ├── goals/
│   │   ├── memory/
│   │   └── ...
│   └── providers/                # React providers (legacy location)
│       ├── auth-provider.tsx
│       └── theme-provider.tsx
│
├── hooks/                        # Custom React hooks
│   ├── use-agents.ts
│   ├── use-goals.ts
│   ├── use-auth.ts
│   ├── use-websocket.ts
│   └── ...
│
├── services/                     # API services
│   ├── api-client.ts             # Centralized HTTP client
│   ├── auth.service.ts
│   ├── agents.service.ts
│   ├── goals.service.ts
│   └── ...
│
├── stores/                       # Zustand state management
│   ├── ui.store.ts
│   ├── agents.store.ts
│   ├── goals.store.ts
│   └── ...
│
├── providers/                    # React context providers
│   ├── auth-provider.tsx
│   ├── theme-provider.tsx
│   └── ...
│
├── types/                        # TypeScript type definitions
│   └── index.ts
│
└── lib/                          # Utilities
    ├── utils.ts
    ├── animations.ts
    └── ...
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | Next.js 15 | App Router, SSR, RSC |
| **UI Library** | React 19 | Component library |
| **Language** | TypeScript 5 | Type safety |
| **Styling** | Tailwind CSS 4 | Utility-first CSS |
| **State Management** | Zustand + TanStack Query | Global state + server state |
| **Animations** | Framer Motion | Smooth animations |
| **Real-time** | SSE + WebSocket | Event streaming |
| **Testing** | Jest + Playwright | Unit + E2E tests |
| **Linting** | ESLint + Prettier | Code quality |

## State Management Strategy

### 1. Local State (`useState`)

**When to use:**
- Component-specific UI state
- Form inputs
- Toggle states

**Example:**
```tsx
const [isOpen, setIsOpen] = useState(false);
```

### 2. URL State (`useSearchParams`)

**When to use:**
- Shareable filters
- Pagination
- Search queries

**Example:**
```tsx
const [search, setSearch] = useSearchParams();
const query = search.get("q") || "";
```

### 3. Server State (TanStack Query)

**When to use:**
- Data from API
- Caching
- Background refetching
- Optimistic updates

**Example:**
```tsx
const { data, isLoading } = useQuery({
  queryKey: ["agents"],
  queryFn: () => agentsService.getAll(),
});
```

### 4. Global State (Zustand)

**When to use:**
- Shared UI state (sidebar, theme)
- Auth state
- Real-time data (WebSocket updates)

**Example:**
```tsx
const { sidebarExpanded, toggleSidebar } = useUIStore();
```

## Data Flow

```
Component
  ├─ useState (local)
  ├─ useSearchParams (URL)
  ├─ useQuery (TanStack Query) ← API
  ├─ useStore (Zustand) ← Global state
  └─ WebSocket/SSE (real-time)
```

## API Integration

### Client Architecture

```ts
services/api-client.ts
├── ApiClient class
│   ├── request<T>() — Generic HTTP method
│   ├── Auth interceptors
│   ├── Error handling
│   └── Token refresh
│
└── Service modules
    ├── authService
    ├── agentsService
    ├── goalsService
    ├── memoryService
    ├── skillsService
    ├── fluxService
    └── settingsService
```

### Usage

```tsx
import { agentsService } from "@/services/api-client";

// In a hook or component
const agents = await agentsService.getAll();
```

## Component Architecture

### UI Components (shadcn-style)

**Location:** `components/ui/`

**Characteristics:**
- Atomic, reusable
- Accessible (ARIA labels, keyboard nav)
- Customizable via `className`
- No business logic

**Example:**
```tsx
<Button variant="primary" size="lg" onClick={handleClick}>
  Click me
</Button>
```

### Feature Components

**Location:** `components/features/`

**Characteristics:**
- Business logic
- Composed of UI components
- Connected to stores/hooks

**Example:**
```tsx
function AgentCard({ agent }: { agent: Agent }) {
  const { deleteAgent } = useDeleteAgent();
  
  return (
    <Card>
      <h3>{agent.name}</h3>
      <Button onClick={() => deleteAgent(agent.id)}>Delete</Button>
    </Card>
  );
}
```

### Layout Components

**Location:** `components/layouts/`

**Characteristics:**
- Structural (sidebar, topbar, inspector)
- Persistent across pages
- Connected to UI store

## Routing Strategy

### Route Groups

```
app/
├── (auth)/                    # Authentication pages
│   ├── login/page.tsx
│   └── layout.tsx
│
├── (dashboard)/               # Protected dashboard
│   ├── layout.tsx             # Dashboard layout
│   ├── page.tsx               # Home
│   ├── agents/
│   ├── goals/
│   └── ...
│
└── layout.tsx                 # Root layout
```

**Benefits:**
- Multiple layouts without nesting
- Shared providers per group
- Clean URL structure

## Provider Hierarchy

```
RootLayout
├── ThemeProvider
│   ├── AuthProvider
│   │   ├── QueryProvider (TanStack Query)
│   │   │   ├── ToastProvider
│   │   │   │   └── children
```

**Order matters:**
1. Theme — CSS variables, dark/light mode
2. Auth — User state, token management
3. Query — Server state caching
4. Toast — Notifications

## Hooks Architecture

### Business Logic Hooks

**Location:** `hooks/`

**Pattern:**
```tsx
export function useAgents() {
  const { agents, isLoading, error, fetchAgents } = useAgentsStore();
  
  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);
  
  return { agents, isLoading, error, refetch: fetchAgents };
}
```

**Benefits:**
- Reusable across components
- Testable in isolation
- Consistent API

### UI Hooks

**Examples:**
- `useMediaQuery` — Responsive design
- `useDebounce` — Input optimization
- `useLocalStorage` — Persistence
- `useKeyboardShortcuts` — Hotkeys

## Styling Strategy

### Tailwind CSS

**Approach:**
- Utility-first classes
- Custom CSS variables for theming
- Component variants with `class-variance-authority`

**Example:**
```tsx
const buttonVariants = cva(
  "base-classes",
  {
    variants: {
      variant: {
        primary: "bg-primary text-white",
        secondary: "bg-secondary text-gray-800",
      },
    },
  }
);
```

### Theme System

**CSS Variables:**
```css
:root {
  --bg-0: #0f172a;
  --fg-0: #f1f5f9;
  --accent: #60a5fa;
  /* ... */
}
```

**Dark/Light Mode:**
- Automatic system preference detection
- Manual override via settings
- Persisted in localStorage

## Performance Optimization

### Code Splitting

- Automatic via Next.js App Router
- Manual with `next/dynamic` for heavy components

### Lazy Loading

```tsx
const HeavyComponent = dynamic(() => import("@/components/heavy"), {
  loading: () => <Skeleton />,
});
```

### Caching

- **TanStack Query** — Server data cache
- **Zustand persist** — UI state persistence
- **localStorage** — User preferences

### Image Optimization

- `next/image` for automatic optimization
- Lazy loading by default
- Responsive images

## Testing Strategy

### Unit Tests

**Tools:** Jest + React Testing Library

**Coverage:**
- Hooks
- Services
- Stores
- Utility functions

### Integration Tests

**Tools:** Jest + React Testing Library

**Coverage:**
- Component interactions
- Provider integration
- Store + component integration

### E2E Tests

**Tools:** Playwright

**Coverage:**
- Critical user flows
- Authentication
- Navigation
- Form submissions

## Accessibility

### Standards

- WCAG 2.1 Level AA
- Keyboard navigation
- Screen reader support
- Reduced motion support

### Implementation

```tsx
// Focus management
<button
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      handleClick();
    }
  }}
/>

// ARIA labels
<button aria-label="Toggle sidebar">...</button>

// Reduced motion
const reducedMotion = useReducedMotion();
```

## Security

### Authentication

- JWT tokens in localStorage
- Automatic token refresh
- 401 handling with redirect

### Authorization

- Role-based access control (RBAC)
- Permission checks in components
- API route protection

### XSS Prevention

- React auto-escaping
- DOMPurify for rich text
- CSP headers

## Internationalization (i18n)

**Library:** next-intl

**Structure:**
```
i18n/
├── index.ts
├── en.json
├── fr.json
└── ...
```

**Usage:**
```tsx
const { t } = useTranslation();
<h1>{t("dashboard.title")}</h1>
```

## Error Handling

### API Errors

```tsx
try {
  await agentsService.create(data);
} catch (error) {
  addToast({
    type: "error",
    message: error.message,
  });
}
```

### Error Boundaries

```tsx
<ErrorBoundary fallback={<ErrorPage />}>
  <App />
</ErrorBoundary>
```

### Toast Notifications

- Success (green)
- Error (red)
- Warning (yellow)
- Info (blue)

## Deployment

### Build

```bash
npm run build
```

**Output:**
- Static pages (SSG)
- Server components (RSC)
- Optimized bundles

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Docker

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Migration Guide

### From Legacy Code

1. **Don't break existing code** — Keep old components working
2. **Incremental migration** — Migrate one feature at a time
3. **Feature flags** — Toggle between old/new implementations
4. **Testing** — Verify behavior before/after migration

### Example Migration

**Before:**
```tsx
// components/old/AgentList.tsx
export function AgentList() {
  // Old implementation
}
```

**After:**
```tsx
// components/features/agents/AgentList.tsx
export function AgentList() {
  const { agents, isLoading } = useAgents();
  // New implementation
}
```

## Best Practices

### Do's ✅

- Use TypeScript strict mode
- Write tests for business logic
- Document complex components
- Use semantic HTML
- Implement keyboard navigation
- Support reduced motion
- Optimize images
- Lazy load heavy components

### Don'ts ❌

- Don't use `any` type
- Don't skip error handling
- Don't hardcode API URLs
- Don't mutate state directly
- Don't forget accessibility
- Don't ignore performance
- Don't skip tests
- Don't commit secrets

## Troubleshooting

### Common Issues

**Build fails:**
```bash
# Clear cache
rm -rf .next
npm run build
```

**Type errors:**
```bash
# Check TypeScript
npx tsc --noEmit
```

**State not updating:**
- Check Zustand store subscription
- Verify immutability
- Check React DevTools

## Contributing

### Adding a New Feature

1. Create feature folder: `components/features/my-feature/`
2. Create store: `stores/my-feature.store.ts`
3. Create hooks: `hooks/use-my-feature.ts`
4. Create page: `app/(dashboard)/my-feature/page.tsx`
5. Add navigation item in `components/layouts/sidebar.tsx`
6. Write tests
7. Update documentation

### Code Review Checklist

- [ ] TypeScript strict mode passes
- [ ] Tests written and passing
- [ ] Accessibility verified
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] Error handling implemented

## License

MIT — See LICENSE file for details