import * as React from "react"

function Tooltip({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="tooltip"
      className={`absolute z-50 rounded-md border border-line-2 bg-elevated px-3 py-1.5 text-xs text-foreground shadow-lg ${className ?? ""}`}
      {...props}
    />
  )
}

export { Tooltip }