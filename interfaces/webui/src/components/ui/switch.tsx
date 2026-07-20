import * as React from "react"

function Switch({ className, checked, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { checked?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`inline-flex h-5 w-9 items-center rounded-full border border-line-2 bg-bg-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${className ?? ""}`}
      {...props}
    >
      <span
        className={`inline-block h-3 w-3 rounded-full bg-foreground-tertiary transition-transform ${checked ? "translate-x-4 bg-accent" : "translate-x-1"}`}
      />
    </button>
  )
}

export { Switch }