"use client";

/**
 * ETHAN WebUI — Motion Design System (source unique).
 *
 * Règles non négociables :
 *  - `framer-motion` est déjà présent : aucune dépendance supplémentaire.
 *  - Les tokens sont la seule source de durées/courbes ; les composants ne
 *    codent jamais une durée en dur.
 *  - `prefers-reduced-motion` est respecté à deux niveaux : `MotionConfig`
 *    (framer) et la feuille globale (animations CSS).
 *  - Aucune animation permanente, aucun décalage artificiel : le motion
 *    accompagne un changement d'état réel (chargement, apparition, filtre).
 *
 * Les helpers purs (`resolveMotion`, `staggerStyle`, `staggerDelay`) sont
 * testables sans DOM ; le hook `useMotionPreset` est réservé aux composants.
 */

import * as React from "react";
import { useReducedMotion } from "framer-motion";
import type { Transition, Variants } from "framer-motion";

/** Durées en secondes (API framer-motion). */
export const DURATION = {
	instant: 0.12,
	fast: 0.16,
	normal: 0.24,
	slow: 0.32,
	entrance: 0.28,
	exit: 0.18,
} as const;

/** Courbes d'accélération (bezier à quatre points, format framer). */
export const EASING: Record<"standard" | "emphasized" | "exit", [number, number, number, number]> = {
	standard: [0.2, 0.8, 0.25, 1],
	emphasized: [0.16, 1, 0.3, 1],
	exit: [0.4, 0, 1, 1],
};

/** Distances d'entrée en pixels. */
export const DISTANCE = {
	xs: 4,
	sm: 8,
	md: 12,
} as const;

/** Pas de décalage séquentiel (secondes pour framer, ms pour le CSS). */
export const STAGGER = {
	tight: 0.02,
	normal: 0.04,
	loose: 0.06,
	/** Plafond : au-delà, l'attente perçue devient artificielle. */
	maxIndex: 12,
} as const;

export interface MotionProfile {
	/** Durées nulles et distances nulles : aucun mouvement. */
	reduced: boolean;
	duration: (seconds: number) => number;
	distance: (pixels: number) => number;
}

/**
 * Profil de mouvement pur, indépendant de React.
 *
 * En mode réduit, la durée devient 0 (et non « presque 0 ») : framer saute
 * directement à l'état final, ce qui évite un flash de contenu translaté.
 */
export function resolveMotion(reduced: boolean): MotionProfile {
	return {
		reduced,
		duration: (seconds) => (reduced ? 0 : seconds),
		distance: (pixels) => (reduced ? 0 : pixels),
	};
}

/**
 * Délai séquentiel plafonné, en millisecondes.
 *
 * Le plafond évite qu'une liste de 150 éléments attende plusieurs secondes :
 * au-delà de `maxIndex`, tous les éléments partagent le même délai maximal.
 */
export function staggerDelay(index: number, stepMs = 28, maxIndex = STAGGER.maxIndex): number {
	const safeIndex = Number.isFinite(index) ? Math.max(0, Math.floor(index)) : 0;
	return Math.min(safeIndex, maxIndex) * stepMs;
}

export type MotionStyle = React.CSSProperties & {
	"--motion-index"?: number;
	"--motion-step"?: string;
};

/**
 * Style inline pour les animations CSS séquencées.
 *
 * On préfère le CSS aux composants framer pour les grandes listes (graphe,
 * timeline, résultats) : une seule animation composited par élément, sans
 * arbre React supplémentaire.
 */
export function staggerStyle(index: number, stepMs = 28, maxIndex = STAGGER.maxIndex): MotionStyle {
	const safeIndex = Number.isFinite(index) ? Math.max(0, Math.floor(index)) : 0;
	return {
		"--motion-index": Math.min(safeIndex, maxIndex),
		"--motion-step": `${stepMs}ms`,
	};
}

/** Variante d'entrée : fondu + translation verticale courte. */
export function fadeUp(reduced: boolean, distance: number = DISTANCE.sm): Variants {
	const profile = resolveMotion(reduced);
	return {
		hidden: { opacity: 0, y: profile.distance(distance) },
		visible: {
			opacity: 1,
			y: 0,
			transition: { duration: profile.duration(DURATION.normal), ease: EASING.standard },
		},
	};
}

/** Variante d'entrée : fondu + échelle très légère (cartes, panneaux). */
export function scaleIn(reduced: boolean): Variants {
	const profile = resolveMotion(reduced);
	return {
		hidden: { opacity: 0, scale: reduced ? 1 : 0.98 },
		visible: {
			opacity: 1,
			scale: 1,
			transition: { duration: profile.duration(DURATION.fast), ease: EASING.emphasized },
		},
	};
}

/** Conteneur séquentiel : les enfants portent `fadeUp`/`scaleIn`. */
export function staggerContainer(reduced: boolean, stagger: number = STAGGER.normal): Variants {
	return {
		hidden: {},
		visible: {
			transition: {
				staggerChildren: reduced ? 0 : stagger,
				delayChildren: reduced ? 0 : 0.02,
			},
		},
	};
}

/** Transition standard réutilisable (panneaux, boutons, survols animés). */
export function standardTransition(reduced: boolean): Transition {
	return {
		duration: resolveMotion(reduced).duration(DURATION.fast),
		ease: EASING.standard,
	};
}

/**
 * Hook de composition : un seul appel par composant, profil + variantes.
 * `useReducedMotion` peut renvoyer `null` avant hydratation : on considère
 * alors « mouvement autorisé » pour ne pas figer l'UI par défaut.
 */
export function useMotionPreset() {
	const reduced = useReducedMotion() ?? false;

	return React.useMemo(
		() => ({
			reduced,
			fadeUp: fadeUp(reduced),
			scaleIn: scaleIn(reduced),
			staggerContainer: staggerContainer(reduced),
			transition: standardTransition(reduced),
		}),
		[reduced],
	);
}
