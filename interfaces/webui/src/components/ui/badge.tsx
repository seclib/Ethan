import * as React from "react"

function Badge({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={`inline-flex items-center rounded-md border border-line-2 bg-bg-2 px-2 py-0.5 text-xs font-medium text-foreground ${className ?? ""}`}
      {...props}
    />
  )
}

export { Badge }