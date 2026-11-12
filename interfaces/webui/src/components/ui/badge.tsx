import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-foreground-tertiary/20 text-foreground-secondary",
        secondary:
          "border-line-2 bg-background text-foreground-secondary",
        accent:
          "border-accent-line bg-accent-soft text-accent",
        success:
          "border-green-soft bg-green-soft text-green",
        warning:
          "border-amber-soft bg-amber-soft text-amber",
        error:
          "border-red-soft bg-red-soft text-red",
        info:
          "border-accent-line bg-accent-soft text-accent",
        dim:
          "border-line-1 bg-line-1 text-foreground-tertiary",
        gold:
          "border-gold-soft bg-gold-soft text-gold",
        purple:
          "border-purple-soft bg-purple-soft text-purple",
        solid:
          "border-accent bg-accent text-white",
      },
      size: {
        sm: "px-1.5 py-0.5 text-[10px]",
        md: "px-2 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean
}

function Badge({ className, variant, size, dot, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(badgeVariants({ variant, size }), "relative", className)}
      {...props}
    >
      {dot && (
        <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" />
      )}
      {children}
    </span>
  )
}

export { Badge, badgeVariants }