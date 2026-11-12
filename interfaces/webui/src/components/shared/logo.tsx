"use client";

/**
 * Logo ETHAN — composant centralisé.
 * Source unique : /ethan-logo.png (public/). Ne jamais référencer
 * l'image directement ailleurs ; passer par ce composant.
 * Format : carré 400x400 (ratio 1:1) — ne jamais déformer.
 */

import Image from "next/image";

interface LogoProps {
  /** Taille du carré en px (le logo est carré 1:1) */
  size?: number;
  className?: string;
  priority?: boolean;
}

export function Logo({ size = 40, className = "", priority = false }: LogoProps) {
  return (
    <Image
      src="/ethan-logo.png"
      alt="ETHAN"
      width={size}
      height={size}
      priority={priority}
      className={`object-cover rounded ${className}`}
      style={{ width: size, height: size }}
    />
  );
}

/** Variante carrée (favicon-like) pour les emplacements compacts. */
export function LogoSquare({
  size = 32,
  className = "",
  priority = false,
}: {
  size?: number;
  className?: string;
  priority?: boolean;
}) {
  return (
    <Image
      src="/ethan-logo.png"
      alt="ETHAN"
      width={size}
      height={size}
      priority={priority}
      className={`object-cover rounded ${className}`}
      style={{ width: size, height: size }}
    />
  );
}