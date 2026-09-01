"use client";

/**
 * Logo ASCII du terminal d'authentification ETHAN.
 * Crâne glitch en caractères — rendu en <pre> monospace, net à toute
 * résolution et cohérent avec le thème terminal de la page de login.
 * (Dérivé de l'image de référence fournie ; aucune ressource binaire.)
 */

const SKULL_LINES = [
  "       ▄▄▓▓?▓▓▓?▄▄       ",
  "    ▄▓#▓▓▓%▓▓?▓▓▓!▓▄    ",
  "   ▐▓▓9▓7▓!▓?▓▓1▓▓▓▓▌   ",
  "  ▓▓▓▓▓#▓▓▓▓?▓▓▓▓!▓▓▓▓  ",
  " ▓▓▓▓▓▓9▓▓▓▓▓▓x▓▓▓▓▓▓▓ ",
  " ▓▓   !?  ▓▓▓▓  ?!   ▓▓ ",
  " ▓▓▓  97   ▓▓   31  ▓▓▓ ",
  " ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ ",
  " ▓▓▓▓▓▓▓▓▓ /\\ ▓▓▓▓▓▓▓▓▓ ",
  " ▓▓M▓▓▓x▓▓▓▓T▓▓▓▓▓Q▓▓▓▓ ",
  " ▓▓▓9▓▓▓▓▓?▓▓▓▓▓!▓▓▓▓ ",
  "  ▀▓▓▓▓?▓▓▓▓▓▓▓?▓▓▓▀  ",
  "     ▐▓!▓▓?▓▓!▓▓?▓▓▌    ",
  "       ▀▓▓?▓▓▓▓?▓▓▀      ",
];

export function AsciiSkull({ className = "" }: { className?: string }) {
  return (
    <pre aria-hidden className={`ascii-skull select-none ${className}`}>
      {SKULL_LINES.join("\n")}
    </pre>
  );
}
