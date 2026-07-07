export const animations = {
  duration: {
    instant: "0ms",
    fast: "100ms",
    normal: "150ms",
    medium: "200ms",
    slow: "300ms",
    slower: "500ms",
  },

  easing: {
    standard: "cubic-bezier(0.4, 0, 0.2, 1)",
    decelerate: "cubic-bezier(0.16, 1, 0.3, 1)",
    smooth: "cubic-bezier(0.25, 0.1, 0.25, 1)",
    snappy: "cubic-bezier(0.2, 0.8, 0.2, 1)",
  },

  page: {
    enter: "200ms cubic-bezier(0.16, 1, 0.3, 1)",
    exit: "150ms ease-in",
  },

  modal: {
    enter: "250ms cubic-bezier(0.16, 1, 0.3, 1)",
    exit: "200ms ease-in",
  },

  button: {
    hover: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    active: "100ms ease-out",
  },

  card: {
    hover: "200ms cubic-bezier(0.4, 0, 0.2, 1)",
    drag: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  },

  toast: {
    enter: "300ms cubic-bezier(0.16, 1, 0.3, 1)",
    exit: "200ms ease-in",
  },

  sidebar: {
    open: "300ms cubic-bezier(0.16, 1, 0.3, 1)",
    close: "200ms ease-in",
  },
} as const;

export type AnimationToken = typeof animations;