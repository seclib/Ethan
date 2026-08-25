# RFC-0003 — Cookbook ETHAN (recettes de workflows)

## Date
2026-08-24

## Statut
✅ **Implémenté** — voir les sections ci-dessous pour l'architecture livrée.

## Résumé
Bibliothèque de « recettes » : workflows préconfigurés (prompts,
skills, tools, paramètres) installables en un clic et partageables —
l'équivalent des presets Odysseus, adossé aux capacités natives ETHAN.

## Origine
Odysseus (cookbook*.js, presets.js). ETHAN possède déjà les briques :
skills (`/v1/skills`), prompts (`/v1/prompts`), automations
(`/v1/automations`), pipelines tools. Il manque le format de paquet
et l'UI d'installation.

## Architecture cible
```
core/cookbook/              ← CookbookManager : manifest, validation, installation atomique
interfaces/api/routers/…    ← GET /v1/cookbook/recipes, POST /v1/cookbook/install, DELETE uninstall
interfaces/webui /cookbook  ← UI : galerie de recettes, détails, installation en 1 clic
```

## Format recette (manifest JSON)
```json
{
  "id": "weekly-report",
  "name": "Rapport hebdomadaire",
  "version": "1.0.0",
  "requires": {"skills": [], "tools": ["builtin_web_search"]},
  "installs": {
    "prompt": {...},
    "skill": {...},
    "automation": {...}
  }
}
```

## Portée proposée
1. **Core** — `CookbookManager` : validation de manifest (schéma),
   installation transactionnelle (rollback si étape échoue),
   désinstallation propre, registre local des recettes installées.
2. **API** — routes minces au-dessus du manager ; RBAC WRITE.
3. **WebUI** — page `/cookbook` : galerie filtrable, fiche détail
   (ce que la recette installe), bouton Installer/Désinstaller.
4. **Sécurité** — une recette n'exécute jamais de code : elle ne
   crée que des enregistrements (skills/prompts/automations) validés.

## Hors portée
- Marketplace distant signé (phase 2) ; import/export fichier.
