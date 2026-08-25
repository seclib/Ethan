"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface PopoverProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
}

interface PopoverContextType {
	open: boolean;
	setOpen: (open: boolean) => void;
}

const PopoverContext = React.createContext<PopoverContextType | undefined>(undefined);

export function Popover({ open, onOpenChange, children }: PopoverProps & { children: React.ReactNode }) {
	return (
		<PopoverContext.Provider value={{ open, setOpen: onOpenChange }}>
			<div className="relative inline-block">{children}</div>
		</PopoverContext.Provider>
	);
}

export function PopoverTrigger({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) {
	const ctx = React.useContext(PopoverContext);
	if (!ctx) return null;
	if (asChild) return <>{children}</>;
	return (
		<button
			onClick={() => ctx.setOpen(!ctx.open)}
			aria-expanded={ctx.open}
			aria-haspopup="true"
			className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50"
		>
			{children}
		</button>
	);
}

export function PopoverContent({ children, align = "end", className, ...props }: {
	children: React.ReactNode;
	align?: "start" | "center" | "end";
	className?: string;
} & React.HTMLAttributes<HTMLDivElement>) {
	const ctx = React.useContext(PopoverContext);
	React.useEffect(() => {
		if (!ctx?.open) return;
		const handleOutside = () => ctx.setOpen(false);
		const handleEsc = (e: KeyboardEvent) => { if (e.key === "Escape") ctx.setOpen(false); };
		document.addEventListener("mousedown", handleOutside);
		document.addEventListener("keydown", handleEsc);
		return () => {
			document.removeEventListener("mousedown", handleOutside);
			document.removeEventListener("keydown", handleEsc);
		};
	}, [ctx]);

	if (!ctx || !ctx.open) return null;

	const alignClass = { start: "left-0", center: "left-1/2 -translate-x-1/2", end: "right-0" }[align];

	return (
		<div className={cn("absolute z-50 mt-2 w-64 rounded-md border border-line-2 bg-background shadow-lg", alignClass, className)} {...props}>
			{children}
		</div>
	);
}
