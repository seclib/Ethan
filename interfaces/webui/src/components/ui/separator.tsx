import * as React from "react"

function Separator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="separator"
      className={`shrink-0 bg-line-2 h-[1px] w-full ${className ?? ""}`}
      {...props}
    />
  )
}

export { Separator }