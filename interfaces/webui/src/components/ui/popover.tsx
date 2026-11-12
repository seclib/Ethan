"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useOverlayStore } from "@/store/overlay.store";

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
	const popoverIdRef = React.useRef(`popover-${Math.random().toString(36).slice(2)}`);
	const onOpenChangeRef = React.useRef(onOpenChange);
	onOpenChangeRef.current = onOpenChange;

	// Pile ESC centralisée : le popover se ferme via le handler global quand il
	// est le sommet de la pile (ouverture → push, fermeture → unregister).
	React.useEffect(() => {
		if (!open) return;
		const unregister = useOverlayStore.getState().push({
			id: popoverIdRef.current,
			onClose: () => onOpenChangeRef.current(false),
		});
		return unregister;
	}, [open]);

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
		// L'Escape est délégué à la pile ESC centralisée (OverlayEscHandler).
		document.addEventListener("mousedown", handleOutside);
		return () => {
			document.removeEventListener("mousedown", handleOutside);
		};
	}, [ctx]);

	if (!ctx || !ctx.open) return null;

	const alignClass = { start: "left-0", center: "left-1/2 -translate-x-1/2", end: "right-0" }[align];

	return (
		<div className={cn("absolute z-popover mt-2 w-64 rounded-md border border-line-2 bg-background shadow-lg", alignClass, className)} {...props}>
			{children}
		</div>
	);
}
