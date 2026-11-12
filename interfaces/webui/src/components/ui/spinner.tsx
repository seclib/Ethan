import * as React from "react"

function Spinner({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="status"
      aria-label="Chargement"
      className={`inline-flex h-4 w-4 animate-spin rounded-full border-2 border-line-2 border-t-accent ${className ?? ""}`}
      {...props}
    />
  )
}

export { Spinner }