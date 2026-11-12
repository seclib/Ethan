/**
 * Garde-fou build Next.js — `useSearchParams()` et frontière `<Suspense>`.
 *
 * Symptôme (build Docker `ui` en échec) :
 *   useSearchParams() should be wrapped in a suspense boundary at page "/404"
 *   Error occurred prerendering page "/_not-found"
 *
 * Cause : `useSearchParams()` provoque un CSR bailout. Toute route prérendue
 * statiquement — donc TOUTE page dont le shell ne déclare pas de frontière
 * `<Suspense>` autour du hook — échoue au build. `/404` et `/_not-found` sont
 * des routes statiques par nature : elles subissent le shell partagé.
 *
 * Règle vérifiée ici (invariant structurel, pas un test d'exécution) :
 *  1. aucun fichier de `src/` ne peut appeler `useSearchParams()` sans être
 *     couvert par une frontière `<Suspense>` (dans le fichier lui-même, ou via
 *     un parent qui l'importe et l'enveloppe) ;
 *  2. le shell partagé (layout racine + sidebar) ne doit PAS appeler le hook
 *     directement : il est rendu sur toutes les routes, donc une régression
 *     ici casse le build entier.
 *
 * Test statique : il couvre l'arbre de rendu complet (layout, providers,
 * widgets), pas seulement une page — même approche que le lint des liens
 * internes (`internal-links.test.ts`).
 */
import fs from "fs";
import path from "path";

const WEBUI_ROOT = path.resolve(__dirname, "../../..");
const SRC_DIR = path.join(WEBUI_ROOT, "src");

/** Fichiers du shell partagé : rendus sur TOUTES les routes. */
const SHELL_FILES = [
  path.join("app", "layout.tsx"),
  path.join("components", "layout", "sidebar.tsx"),
];

/** Retire les commentaires pour ne pas lire la documentation comme du code. */
function stripComments(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

function listSourceFiles(dir: string): string[] {
  const found: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...listSourceFiles(abs));
    } else if (/\.tsx?$/.test(entry.name)) {
      found.push(abs);
    }
  }
  return found;
}

/** Résout un specifier d'import relatif vers un chemin absolu (sans extension). */
function resolveRelative(fromFile: string, specifier: string): string | null {
  if (!specifier.startsWith(".")) return null;
  const base = path.resolve(path.dirname(fromFile), specifier);
  for (const candidate of [base, `${base}.ts`, `${base}.tsx`]) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      return candidate;
    }
  }
  return null;
}

const FILES = listSourceFiles(SRC_DIR);

const HOOK_CALLERS = FILES.filter((file) =>
  stripComments(fs.readFileSync(file, "utf-8")).includes("useSearchParams("),
);

const SUSPENSE_OWNERS = new Set(
  FILES.filter((file) => fs.readFileSync(file, "utf-8").includes("<Suspense")),
);

/** Un fichier est « couvert » s'il déclare lui-même la frontière ou est importé par un parent qui la déclare. */
function isCoveredBySuspense(file: string): boolean {
  if (SUSPENSE_OWNERS.has(file)) return true;
  return FILES.some((candidate) => {
    if (candidate === file) return false;
    const source = fs.readFileSync(candidate, "utf-8");
    if (!source.includes("<Suspense")) return false;
    const importRegex = /from\s+"([^"]+)"/g;
    let match: RegExpExecArray | null;
    while ((match = importRegex.exec(source)) !== null) {
      const resolved = resolveRelative(candidate, match[1]);
      if (resolved === file) return true;
    }
    return false;
  });
}

describe("build Next.js — useSearchParams() sous frontière Suspense", () => {
  it("le code source contient bien des appels à useSearchParams() (garde-fou non vide)", () => {
    expect(HOOK_CALLERS.length).toBeGreaterThan(0);
  });

  it.each(HOOK_CALLERS.map((file) => [path.relative(WEBUI_ROOT, file), file] as const))(
    "%s appelle useSearchParams() sous une frontière <Suspense>",
    (_label, file) => {
      expect(isCoveredBySuspense(file)).toBe(true);
    },
  );

  it.each(SHELL_FILES)("le shell partagé %s n'appelle pas useSearchParams() directement", (relative) => {
    const absolute = path.join(SRC_DIR, relative);
    expect(fs.existsSync(absolute)).toBe(true);
    const source = stripComments(fs.readFileSync(absolute, "utf-8"));
    expect(source).not.toContain("useSearchParams(");
  });
});
