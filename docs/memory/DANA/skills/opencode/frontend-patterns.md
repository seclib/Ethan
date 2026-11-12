# Frontend Patterns (frontend-patterns)

**Source :** `/home/fatsio/.config/opencode/skills/frontend-patterns/SKILL.md`  \n**Domaine :** Frontend — React/Next.js  \n**Type :** Skill technique  \n**Niveau :** Indispensable (Niveau A)  \n

## Description

Production-ready animation patterns for React/Next.js — button, modal, toast, stagger, page transitions, exit animations, scroll, layout. Built on motion-foundations tokens and springs. Covers component patterns (composition, compound, controlled/uncontrolled forms), state management (useState, useReducer, Context, Zustand, Redux), data fetching (SWR, React Query, server components), performance optimization (memoization, virtualization, code splitting), and accessibility.

## Main capabilities

- **Animation patterns**: Implements button, modal, toast, stagger, page transitions, exit animations
- **Component patterns**: Composition, compound components, controlled/uncontrolled forms
- **State management**: useState, useReducer, Context API, Zustand, Redux integration
- **Data fetching**: SWR, React Query, React Server Components integration
- **Performance optimization**: Memoization, virtualization, code splitting
- **Accessibility**: ARIA roles, keyboard navigation, screen reader support

## What it can do

- Create animated UI components (buttons, modals, toasts) with motion principles
- Implement compound component patterns for complex UI
- Set up state management with Context, Redux, or Zustand
- Integrate data fetching with SWR or React Query
- Apply memoization (memo, useMemo) and virtualization (react-virtual)
- Optimize performance with code splitting and lazy loading
- Ensure accessibility with proper ARIA roles and keyboard navigation

## When it is useful

- Building new React/Next.js applications with consistent UI patterns
- Animating UI elements with natural, spring-based motion
- Implementing toast notifications and modal dialogs
- Setting up state management for medium to large applications
- Optimizing render performance and reducing bundle size
- Adding accessibility support to existing components
- Designing consistent visual language across application

## Practical examples

### Animated button with spring

```jsx
import { motion } from "framer-motion";

export const AnimatedButton = ({ onClick, children }) => (
  <motion.button
    onClick={onClick}
    whileHover={{ scale: 1.05 }}
    whileTap={{ scale: 0.98 }}
    transition={{ type: "spring", stiffness: 400, damping: 20 }}
  >
    {children}
  </motion.button>
);
```

### Compound component pattern

```jsx
// Select component with composition
const Select = ({ children, value, onChange }) => (
  <div className="select">
    <SelectTrigger>
      <SelectValue>{value}</SelectValue>
      <SelectArrow />
    </SelectTrigger>
    <SelectMenu>
      {children.map(child => child)}
    </SelectMenu>
  </div>
);

// Usage
<Select value="option1" onChange={setValue}>
  <SelectOption value="option1">Option 1</SelectOption>
  <SelectOption value="option2">Option 2</SelectOption>
</Select>
```

### SWR data fetching

```jsx
import useSWR from "swr";

export const useUserData = (userId) => {
  const { data, error, isLoading } = useSWR(`/api/users/${userId}`, fetcher);
  return { user: data, isLoading, isError: error };
};
```

## Original source path

`/home/fatsio/.config/opencode/skills/frontend-patterns/SKILL.md`

## Classification

- **Domaines :** frontend, React, Next.js, animation, état, accessibility
- **Statut :** Indispensable (Niveau A)
- **Références :** `motion-patterns`, `python-pro`, `api-design`
- **Validé :** Oui (rapport d'analyse stratégique Niveau A)
- **Auteur :** OpenCode Analysis
