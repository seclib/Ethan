"use client";

import { create } from "zustand";

export interface OverlayItem {
  /** Identifiant stable de la couche (idempotence des push répétés). */
  id: string;
  /** Rappel exécuté lorsque la couche est fermée par ESC global. */
  onClose: () => void;
}

interface OverlayStoreState {
  /** Pile LIFO des couches ouvertes. Le sommet = dernière couche ouverte. */
  stack: OverlayItem[];
  /**
   * Enregistre une couche. Idempotent par id : un push répété remplace la
   * position de la couche au sommet au lieu de la dupliquer.
   * Renvoie la fonction de désenregistrement (appelée au unmount/close).
   */
  push: (item: OverlayItem) => () => void;
  remove: (id: string) => void;
  /** Ferme uniquement la couche la plus haute. */
  closeTop: () => void;
}

let fallbackId = 0;

export const useOverlayStore = create<OverlayStoreState>((set, get) => ({
  stack: [],
  push: (item) => {
    const id = item.id || `overlay-${fallbackId++}`;
    set((s) => ({
      // Remplace la couche existante du même id (la déplace au sommet).
      stack: [...s.stack.filter((i) => i.id !== id), { ...item, id }],
    }));
    return () => get().remove(id);
  },
  remove: (id) =>
    set((s) => ({ stack: s.stack.filter((i) => i.id !== id) })),
  closeTop: () => {
    const stack = get().stack;
    const top = stack[stack.length - 1];
    if (!top) return;
    // LIFO pur : retire d'abord la couche, puis exécute le rappel — un ESC ne
    // ferme qu'une seule couche, même si le rappel ne ferme rien.
    // Le `remove` du cleanup React reste idempotent (filter).
    set((s) => ({ stack: s.stack.filter((i) => i.id !== top.id) }));
    top.onClose();
  },
}));