import * as React from "react"

function Table({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-auto">
      <table className={`w-full caption-bottom text-sm text-foreground ${className ?? ""}`} {...props} />
    </div>
  )
}

function TableHeader({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={`border-b border-line-2 ${className ?? ""}`} {...props} />
  )
}

function TableBody({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={`[&_tr:last-child]:border-0 ${className ?? ""}`} {...props} />
  )
}

function TableRow({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={`border-b border-line-1 transition-colors ${className ?? ""}`} {...props} />
  )
}

function TableCell({ className, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`p-3 align-middle ${className ?? ""}`} {...props} />
  )
}

function TableHead({ className, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={`p-3 text-left font-medium text-foreground-secondary ${className ?? ""}`} {...props} />
  )
}

export { Table, TableHeader, TableBody, TableRow, TableCell, TableHead }