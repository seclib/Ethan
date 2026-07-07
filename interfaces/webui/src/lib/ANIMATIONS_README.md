# ETHAN WebUI — Animation System

## Overview

A comprehensive animation system inspired by **Jarvis-OS**, **Windows 11**, **Arc Browser**, **Linear**, and **Raycast**. Provides smooth, professional micro-interactions while respecting user accessibility preferences.

## Architecture

```
src/lib/animations.ts      # Design tokens (durations, easings)
src/lib/animations.css     # Keyframes + utility classes
src/hooks/useAnimations.ts # React hooks for motion logic
src/components/ui/         # Animated primitives (Card, Button)
```

## Design Tokens

### Durations

```ts
animations.duration.instant  // 0ms
animations.duration.fast     // 100ms
animations.duration.normal   // 150ms
animations.duration.medium   // 200ms
animations.duration.slow     // 300ms
animations.duration.slower   // 500ms
```

### Easings

```ts
animations.easing.standard   // cubic-bezier(0.4, 0, 0.2, 1)
animations.easing.decelerate // cubic-bezier(0.16, 1, 0.3, 1)
animations.easing.smooth     // cubic-bezier(0.25, 0.1, 0.25, 1)
animations.easing.snappy     // cubic-bezier(0.2, 0.8, 0.2, 1)
```

## CSS Classes

### Animations

| Class | Duration | Easing | Use Case |
|-------|----------|--------|----------|
| `.animate-fade-in` | 200ms | ease-out | General fade in |
| `.animate-fade-out` | 150ms | ease-in | General fade out |
| `.animate-slide-up` | 200ms | decelerate | Content appearing |
| `.animate-slide-down` | 150ms | ease-in | Content disappearing |
| `.animate-scale-in` | 200ms | decelerate | Modals, popovers |

### Hover Effects

| Class | Effect |
|-------|--------|
| `.hover-lift` | TranslateY(-2px) + scale(1.01) + shadow |
| `.card-glow` | Border glow + subtle shadow |
| `.btn-lift` | TranslateY(-1px) + shadow |

### Specialized

| Class | Use Case |
|-------|----------|
| `.skeleton-shimmer` | Loading placeholders |
| `.toast` | Notification enter |
| `.toast-exit` | Notification exit |
| `.card-dragging` | Drag & drop active |
| `.card-drop-target` | Drag & drop target |
| `.widget-appear` | Dashboard widgets |
| `.value-updated` | Metric value flash |

## React Hooks

### `useReducedMotion()`

Detects user preference for reduced motion.

```tsx
const reducedMotion = useReducedMotion();
// Returns true if prefers-reduced-motion: reduce
```

### `usePageTransition(isActive)`

Manages page enter/exit states.

```tsx
const status = usePageTransition(isActive);
// Returns: "idle" | "entering" | "exiting"
```

### `useStagger(items, delay)`

Adds staggered animation delays to list items.

```tsx
const staggeredItems = useStagger(items, 30);
// Returns: [{ item, style: { animationDelay: "0ms" } }, ...]
```

### `useScrollReveal(ref)`

Triggers animation when element enters viewport.

```tsx
const isVisible = useScrollReveal(ref);
// Returns true when element is 10% visible
```

### `useAnimatedCounter(target, duration)`

Animates number counting.

```tsx
const count = useAnimatedCounter(100, 500);
// Smoothly counts from 0 to 100 over 500ms
```

### `useDragAnimation(isDragging, isDropTarget)`

Manages drag & drop visual states.

```tsx
const { isDraggingClass, isDropTargetClass, isDroppedClass } = useDragAnimation(true, false);
```

## Animated Components

### `AnimatedCard`

Card with appear animation and hover glow.

```tsx
<AnimatedCard delay={100} onClick={() => {}}>
  <h3>Title</h3>
  <p>Content</p>
</AnimatedCard>
```

**Props:**
- `children` — Card content
- `className` — Additional CSS classes
- `delay` — Animation delay in ms (default: 0)
- `onClick` — Click handler (optional)

### `AnimatedButton`

Button with lift effect on hover.

```tsx
<AnimatedButton variant="primary" onClick={() => {}}>
  Click me
</AnimatedButton>
```

**Props:**
- `children` — Button text
- `onClick` — Click handler
- `disabled` — Disabled state (default: false)
- `variant` — "primary" | "secondary" | "ghost" (default: "primary")
- `className` — Additional CSS classes

## Usage Examples

### Staggered List

```tsx
function TaskList({ tasks }) {
  const staggeredTasks = useStagger(tasks, 50);

  return (
    <div>
      {staggeredTasks.map(({ item, style }) => (
        <AnimatedCard key={item.id} style={style}>
          <TaskItem task={item} />
        </AnimatedCard>
      ))}
    </div>
  );
}
```

### Scroll Reveal

```tsx
function Dashboard() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const isVisible = useScrollReveal(sectionRef);

  return (
    <div ref={sectionRef} className={isVisible ? "animate-slide-up" : "opacity-0"}>
      <h2>Dashboard</h2>
    </div>
  );
}
```

### Animated Counter

```tsx
function MetricCard({ value, label }) {
  const count = useAnimatedCounter(value, 800);

  return (
    <AnimatedCard>
      <div className="kpi-value">{count}</div>
      <div className="kpi-label">{label}</div>
    </AnimatedCard>
  );
}
```

## Accessibility

### Reduced Motion

All animations automatically respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Hooks check this preference and disable animations accordingly.

### Keyboard Navigation

All animated components maintain keyboard accessibility:
- Focus states are preserved
- No animation traps
- `tabindex` order unchanged

## Performance

### GPU Acceleration

All transforms use GPU-accelerated properties:
- `transform` (translateY, scale)
- `opacity`

Avoid animating:
- `width` / `height`
- `top` / `left`
- `box-shadow` (use sparingly)

### Will-Change

Applied selectively:
```css
.virtual-list {
  will-change: transform;
}
```

### Throttling

Scroll-based animations use `IntersectionObserver` (not scroll events).

## Inspiration

### Jarvis-OS
- Smooth page transitions
- Subtle hover states
- Professional, calm feel

### Windows 11
- Mica material (backdrop blur)
- Rounded corners (12-16px)
- Subtle shadows

### Arc Browser
- Clean, minimal animations
- Fast transitions (150-200ms)
- Staggered reveals

### Linear
- Precise easing curves
- Micro-interactions on every action
- Consistent timing

### Raycast
- Command palette animations
- Toast notifications
- Quick, snappy feel

## Best Practices

### Do's ✅

- Use `AnimatedCard` for content cards
- Use `AnimatedButton` for actions
- Respect `delay` for staggered lists
- Test with `prefers-reduced-motion`
- Keep animations under 300ms

### Don'ts ❌

- Don't animate layout properties (width, height)
- Don't use animations for critical information
- Don't stack more than 3 simultaneous animations
- Don't exceed 500ms duration
- Don't forget disabled states

## Migration Guide

### Before (manual CSS)

```tsx
<div className="card-glow hover-lift">
  <h3>Title</h3>
</div>
```

### After (animated component)

```tsx
<AnimatedCard delay={100}>
  <h3>Title</h3>
</AnimatedCard>
```

## Testing

### Manual

1. Enable "Reduce Motion" in OS settings
2. Verify all animations are disabled
3. Check keyboard navigation still works
4. Test on low-end hardware

### Automated

```tsx
// Example test
test("respects reduced motion", () => {
  render(<AnimatedCard>Test</AnimatedCard>);
  const card = screen.getByText("Test");

  // Should not have animation classes when reduced motion is on
  expect(card).not.toHaveClass("widget-appear");
});
```

## Future Enhancements

- [ ] Spring physics for natural motion
- [ ] Gesture-based animations (drag, swipe)
- [ ] Shared element transitions
- [ ] Animation orchestration (timeline)
- [ ] Lottie integration for complex animations
- [ ] Rive integration for interactive animations

## References

- [Jarvis-OS UI](https://github.com/ethan/Ethan)
- [Windows 11 Fluent Design](https://fluent2.microsoft.design/)
- [Arc Browser](https://arc.net/)
- [Linear Design](https://linear.app/design)
- [Raycast](https://raycast.com/)