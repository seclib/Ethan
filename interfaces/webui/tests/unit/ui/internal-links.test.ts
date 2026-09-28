/**
 * Garde-fou « anti-fantôme » (règle d'architecture ETHAN).
 *
 * Le WebUI ne doit exposer QUE des capacités réelles : un lien interne
 * (`href` / `router.push` / `redirect`) doit correspondre à une route
 * effectivement définie dans l'App Router (`src/app/**​/page.tsx`).
 *
 * Ce test est un lint statique : il scanne le source plutôt que de monter
 * l'application, afin de couvrir aussi les données de navigation, la palette
 * de commandes et les widgets — pas seulement la sidebar.
 *
 * Il couvre les liens littéraux et les templates (`/projects/${id}/files`)
 * en confrontant les « formes » (segments littéraux vs segments dynamiques).
 */
import fs from "fs";
import path from "path";

const WEBUI_ROOT = path.resolve(__dirname, "../../..");
const SRC_DIR = path.join(WEBUI_ROOT, "src");
const APP_DIR = path.join(SRC_DIR, "app");

type Part = { kind: "literal"; value: string } | { kind: "wild" };
type Route = { url: string; parts: Part[]; catchAll: boolean };

/** Découpe une URL en segments typés (littéral ou dynamique). */
function toParts(url: string): Part[] {
  const clean = url.split(/[#?]/)[0];
  return clean
    .split("/")
    .filter((p) => p.length > 0)
    .map<Part>((p) =>
      p.includes("${") || p.startsWith(":") || p.startsWith("…")
        ? { kind: "wild" }
        : { kind: "literal", value: p },
    );
}

/** Construit un segment d'URL depuis un nom de dossier Next.js. */
function segmentToUrlPart(name: string): string {
  if (/^\[\[?\.\.\..+\]\]?$/.test(name)) return ":catchall";
  if (/^\[.+\]$/.test(name)) return `:${name.slice(1, -1)}`;
  return name;
}

/** Parcourt `src/app` et retourne toutes les routes déclarées. */
function collectRoutes(dir: string, parentUrl = ""): Route[] {
  const routes: Route[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const isGroup = entry.name.startsWith("(") && entry.name.endsWith(")");
    const segment = isGroup ? "" : segmentToUrlPart(entry.name);
    const url = `${parentUrl}/${segment}`.replace(/\/{2,}/g, "/");
    const abs = path.join(dir, entry.name);
    if (fs.existsSync(path.join(abs, "page.tsx"))) {
      const parts = toParts(url);
      routes.push({
        url: url === "" ? "/" : url,
        parts,
        catchAll: parts.length > 0 && segment === ":catchall",
      });
    }
    routes.push(...collectRoutes(abs, url));
  }
  return routes;
}

/** Un href correspond-il à cette route ? */
function matchesRoute(hrefParts: Part[], route: Route): boolean {
  const routeParts = route.parts;
  const fixed = route.catchAll ? routeParts.length - 1 : routeParts.length;
  if (route.catchAll) {
    if (hrefParts.length < fixed) return false;
  } else if (hrefParts.length !== routeParts.length) {
    return false;
  }
  for (let i = 0; i < fixed; i += 1) {
    const h = hrefParts[i];
    const r = routeParts[i];
    if (h.kind === "literal" && r.kind === "literal" && h.value !== r.value) return false;
  }
  return true;
}

/** Fichiers source à scanner (composants, données de nav, widgets). */
function walkSource(dir: string, acc: string[] = []): string[] {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const abs = path.join(dir, entry.name);
    if (entry.isDirectory()) walkSource(abs, acc);
    else if (/\.(ts|tsx)$/.test(entry.name)) acc.push(abs);
  }
  return acc;
}

/** href littéral : `href="/x"`, `href: "/x"`, `href={"/x"}` */
const HREF_PATTERN = /href\s*[:=]\s*\{?\s*["'`](\/[^"'`]*)["'`]/g;
/** navigations impératives : `router.push("/x")`, `redirect("/x")` */
const NAV_PATTERN = /(?:router\.(?:push|replace)|redirect)\s*\(\s*["'`](\/[^"'`]*)["'`]/g;

/** Fichiers statiques servis par `public/` (ex. /favicon.ico). */
function isPublicAsset(url: string): boolean {
  const clean = url.split(/[#?]/)[0].replace(/^\//, "");
  return fs.existsSync(path.join(WEBUI_ROOT, "public", clean));
}

const LINK_SOURCE_PATTERNS: RegExp[] = [HREF_PATTERN, NAV_PATTERN];

describe("Liens internes — garde-fou anti-fantôme", () => {
  // `collectRoutes` ne dérive les routes que des DOSSIERS : la page racine
  // (src/app/page.tsx) est donc ajoutée explicitement.
  const routes: Route[] = [
    ...(fs.existsSync(path.join(APP_DIR, "page.tsx"))
      ? [{ url: "/", parts: [] as Part[], catchAll: false }]
      : []),
    ...collectRoutes(APP_DIR),
  ];

  it("découvre l'arbre de routes de l'App Router", () => {
    const urls = routes.map((r) => r.url);
    expect(urls).toContain("/");
    expect(urls).toContain("/settings");
    expect(urls).toContain("/skills");
    expect(urls).toContain("/library");
    expect(urls).toContain("/projects/:id");
    expect(urls.length).toBeGreaterThan(30);
  });

  it("chaque lien interne du source pointe une route réelle", () => {
    const files = walkSource(SRC_DIR);
    const unmatched: string[] = [];
    let inspected = 0;

    for (const file of files) {
      const content = fs.readFileSync(file, "utf8");
      const rel = path.relative(WEBUI_ROOT, file);
      for (const pattern of LINK_SOURCE_PATTERNS) {
        const re = new RegExp(pattern.source, "g");
        let match: RegExpExecArray | null;
        while ((match = re.exec(content)) !== null) {
          const href = match[1];
          inspected += 1;
          if (isPublicAsset(href)) continue;
          const parts = toParts(href);
          if (routes.some((route) => matchesRoute(parts, route))) continue;
          const line = content.slice(0, match.index).split("\n").length;
          unmatched.push(`${rel}:${line} → ${href}`);
        }
      }
    }

    // Garde-fou du garde-fou : si les regex cessent de matcher, le test échoue
    // (sinon un « 0 lien trouvé » passerait silencieusement au vert).
    expect(inspected).toBeGreaterThan(30);
    expect(unmatched).toEqual([]);
  });
});
