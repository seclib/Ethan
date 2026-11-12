/**
 * ETHAN WebUI — Accent color preferences
 *
  * Interface-only concern (ETHAN visual identity). Persists the user's
 * accent choice in localStorage and applies it as an inline CSS custom
 * property override on <html>, winning over any [data-theme] stylesheet rule.
 */

export interface AccentPreset {
	id: string;
	label: string;
	/** RGB triple string ("r g b"), or null = theme default (ETHAN). */
	rgb: string | null;
}

export const ACCENT_STORAGE_KEY = "ethan_accent";

export const ACCENT_PRESETS: AccentPreset[] = [
	{ id: "ethan", label: "ETHAN", rgb: null },
	{ id: "cyan", label: "Cyan", rgb: "86 182 194" },
	{ id: "purple", label: "Purple", rgb: "198 120 221" },
	{ id: "green", label: "Green", rgb: "80 250 123" },
	{ id: "gold", label: "Gold", rgb: "245 158 11" },
	{ id: "blue", label: "Blue", rgb: "97 175 239" },
];

/** Apply (or clear) the accent override on the document root. */
export function applyAccent(rgb: string | null): void {
	if (typeof document === "undefined") return;
	const root = document.documentElement;
	if (!rgb) {
		root.style.removeProperty("--accent-rgb");
	} else {
		root.style.setProperty("--accent-rgb", rgb);
	}
}

/** Persist the accent choice and apply it immediately. */
export function setStoredAccent(preset: AccentPreset): void {
	if (typeof window === "undefined") return;
	if (preset.rgb === null) {
		window.localStorage.removeItem(ACCENT_STORAGE_KEY);
	} else {
		window.localStorage.setItem(ACCENT_STORAGE_KEY, preset.rgb);
	}
	applyAccent(preset.rgb);
}

/** Restore the persisted accent (call once on app bootstrap). */
export function restoreAccent(): void {
	if (typeof window === "undefined") return;
	const stored = window.localStorage.getItem(ACCENT_STORAGE_KEY);
	if (stored) applyAccent(stored);
}

/** Resolve the currently active preset id from storage. */
export function getActiveAccentId(): string {
	if (typeof window === "undefined") return "ethan";
	const stored = window.localStorage.getItem(ACCENT_STORAGE_KEY);
	if (!stored) return "ethan";
	return ACCENT_PRESETS.find((p) => p.rgb === stored)?.id ?? "custom";
}
