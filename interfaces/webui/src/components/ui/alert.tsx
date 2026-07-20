import * as React from "react"

function Alert({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="alert"
      className={`relative w-full rounded-md border border-line-2 bg-surface px-4 py-3 text-sm text-foreground ${className ?? ""}`}
      {...props}
    />
  )
}

function AlertTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h5 className={`mb-1 font-medium leading-none tracking-tight ${className ?? ""}`} {...props} />
  )
}

function AlertDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <div className={`text-foreground-secondary ${className ?? ""}`} {...props} />
  )
}

export { Alert, AlertTitle, AlertDescription }