/**
 * ETHAN WebUI — Pont de vocabulaire des capacités LLM.
 *
 * SOURCE DE VÉRITÉ : ETHAN Core. Aucune capacité n'est inventée ici.
 *
 * Deux vocabulaires réels, exposés par le Core :
 * - capacités PROVIDER (`core/llm/types.py::ProviderCapability`) :
 *   llm, vision, embedding, speech_to_text, transcription — renvoyées par
 *   GET /providers (champ `capabilities`) et GET /providers/catalog ;
 * - capacités MODÈLE (`ModelInfo.capabilities`), métadonnées par modèle
 *   fournies par chaque provider : chat, code, reasoning, vision, embedding…
 *
 * Ce module ne fait que traduire l'AFFICHAGE des valeurs canoniques connues
 * et associer une variante de badge. Toute valeur inconnue est rendue BRUTE,
 * exactement telle que fournie par le Core — jamais renommée ni masquée.
 */

/** Variantes de badge utilisées (sous-ensemble valide de `Badge`). */
export type CapabilityBadgeVariant =
	| "info"
	| "accent"
	| "purple"
	| "success"
	| "gold"
	| "dim";

/** Libellés des capacités provider (vocabulaire canonique ProviderCapability). */
const PROVIDER_CAPABILITY_LABELS: Record<string, string> = {
	llm: "LLM",
	vision: "Vision",
	embedding: "Embeddings",
	speech_to_text: "Speech-to-Text",
	transcription: "Transcription",
};

/** Libellés des capacités modèle (métadonnées provider connues). */
const MODEL_CAPABILITY_LABELS: Record<string, string> = {
	chat: "Chat",
	code: "Code",
	reasoning: "Reasoning",
	vision: "Vision",
	embedding: "Embeddings",
	audio: "Audio",
};

const CAPABILITY_BADGE_VARIANTS: Record<string, CapabilityBadgeVariant> = {
	llm: "info",
	chat: "info",
	code: "info",
	reasoning: "accent",
	vision: "purple",
	embedding: "success",
	speech_to_text: "gold",
	transcription: "gold",
	audio: "gold",
};

/**
 * Libellé d'affichage d'une capacité.
 *
 * Une valeur inconnue est affichée telle quelle (valeur brute Core) : le
 * frontend ne décide jamais quelles capacités existent.
 */
export function capabilityLabel(value: string): string {
	return (
		PROVIDER_CAPABILITY_LABELS[value] ?? MODEL_CAPABILITY_LABELS[value] ?? value
	);
}

/** Variante de badge d'une capacité (dim si valeur inconnue). */
export function capabilityVariant(value: string): CapabilityBadgeVariant {
	return CAPABILITY_BADGE_VARIANTS[value] ?? "dim";
}

/**
 * Union stable des capacités réellement présentes dans une liste de modèles.
 *
 * Utilisé pour construire les filtres de capacités : uniquement des valeurs
 * fournies par le Core, jamais une liste statique inventée côté WebUI.
 */
export function uniqueModelCapabilities(
	models: { capabilities?: string[] }[],
): string[] {
	const seen: string[] = [];
	for (const model of models) {
		for (const capability of model.capabilities ?? []) {
			if (capability && !seen.includes(capability)) seen.push(capability);
		}
	}
	return seen.sort((a, b) => a.localeCompare(b));
}
