# ETHAN Response Renderer — architecture

## Diagnostic initial

- Moteur Markdown précédemment utilisé : `react-markdown` + `remark-gfm`, via `src/components/features/assistant/components/markdown-content.tsx`.
- Rendu des messages assistant dans `assistant-message.tsx`, flux de conversation dans `assistant-chat.tsx`.
- Streaming géré par le chat via mise à jour du contenu du dernier message assistant et indicateur de génération.
- Bibliothèques présentes : React, Next.js, Tailwind, framer-motion, xterm, tanstack-query, zustand. Aucune bibliothèque graphique ou de diagramme n'était installée.
- Nouvelle dépendance justifiée : `rehype-highlight` (mise en évidence syntaxique Markdown), appuyée sur `highlight.js` déjà transitivement disponible.
- Composants existants réutilisés : tokens CSS ETHAN, surfaces, badges, progress, cartes.

## Architecture

Responsabilités séparées :

1. Production du contenu par le modèle, l'agent ou l'outil.
2. Normalisation et validation via `parse-rich-content.ts` et `types.ts`.
3. Rendu des composants via `rich-content.tsx`.
4. Interactions utilisateur : uniquement boutons sans charge privilégiée (copie, détails).

Le renderer est découplé du provider, du modèle et des APIs OpenAI-compatible. Le Markdown standard reste le format de base.

## Format de contenu enrichi

Les composants enrichis utilisent des blocs de code fermés dont l'infostring désigne le type :

````markdown
```chart
{
  "type": "bar",
  "title": "Résultats",
  "data": [
    { "label": "A", "value": 12 },
    { "label": "B", "value": 18 }
  ]
}
```
````

Types pris en charge :

- `callout`
- `chart`
- `kpi`
- `status`
- `details`
- `diagram` (alias `flow`, `architecture`)

Les données doivent être du JSON valide. En cas d'absence, de malformation ou d'inexactitude, le bloc est affiché comme bloc de code normal, ce qui constitue le repli lisible.

Les signatures d'infostring non reconnues restent des blocs de code standard.

## Composants créés ou réutilisés

Créés :

- `rich-response/types.ts`
- `rich-response/parse-rich-content.ts`
- `rich-response/standard-markdown.tsx`
- `rich-response/rich-content.tsx`
- `rich-response/code-block.tsx`
- `rich-response/callout.tsx`
- `rich-response/chart.tsx`
- `rich-response/kpi.tsx`
- `rich-response/status-badge.tsx`
- `rich-response/details.tsx`
- `rich-response/diagram.tsx`

Intégrés :

- `assistant-message.tsx` utilise désormais `RichContent` pour le corps du message assistant.

Composants réutilisés :

- tokens et classes Tailwind existants (`bg`, `surface`, `line`, `accent`, `green`, `gold`, `red`);
- boutons, icônes `lucide-react`.

## Sécurité

- React Markdown échappe le HTML par défaut.
- Les liens sont filtrés par protocole (`http`, `https`, `mailto`, `tel`, ancres, chemins relatifs) ; les liens `javascript:` sont neutralisés.
- Aucune utilisation de `dangerouslySetInnerHTML`.
- Validation stricte des JSON avant rendu.
- Les blocs invalides basculent vers une présentation de code, sans erreur conversationnelle.
- Aucun composant ne déclenche d'action privilégiée.

## Streaming

- Les blocs incomplets (fence non fermée) restent affichés comme Markdown brut pendant la génération.
- Un bloc fermé mais JSON incomplet bascule en code.
- Le rendu final correspond au contenu complet reçu.
- L'auto-scroll et le curseur de génération existants sont conservés.

## Tests et résultats

Commandes exécutées :

- `npm run typecheck` : succès.
- `npm run lint` (cible rich-response) : 0 erreur, 1 avertissement corrigé.
- `npm test -- --runTestsByPath tests/unit/assistant/RichResponseParse.test.ts tests/unit/assistant/RichResponseComponents.test.tsx` : 11 tests réussis.
- `npm run build` : succès.

## Limitations et dette technique

- La coloration syntaxique CSS utilise un thème `atom-one-dark-reasonable`; il peut être remplacé plus tard par un thème aligné exactement avec les tokens ETHAN.
- Les diagrammes utilisent un positionnement automatique simple ; les données avec coordonnées explicites restent prises en charge.
- Aucune dépendance de graphique externe n'a été ajoutée ; les composants restent SVG maison.
- `markdown-content.tsx` reste disponible pour compatibilité, mais n'est plus le chemin principal.
- Le tri interactif des tableaux n'est pas implémenté, conformément à la prudence demandée.
