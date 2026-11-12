# ETHAN — Mémoire technique consolidée

Ce dossier constitue la mémoire technique ETHAN consolidée.

Il rassemble, dans un seul endroit versionnable au besoin, trois familles de ressources distinctes :

1. **Archives** : conversations brutes et rapports d'agents. Ce sont des documents historiques. Ils décrivent ce qui a été dit ou tenté, pas nécessairement ce que le code fait aujourd'hui.
2. **Knowledge** : connaissances synthétisées et vérifiées, conventions, index et synthèses. Elles aident à naviguer dans le projet, mais elles ne remplacent ni le code ni les tests.
3. **Operational-Memory** : état réel, décisions, tâches et blocages. Elle doit décrire uniquement ce qui est confirmé ou explicitement marqué comme incertain.

## Structure

```text
daena/
├── README.md                          # Ce fichier
├── INDEX.md                           # Index consolidé
├── Archives/
│   ├── Conversations/
│   │   ├── cline/
│   │   ├── codex/
│   │   ├── copilot/
│   │   └── from-ethan-knowledge/      # versions préservées uniquement dans Source A
│   └── Rapports-Agents/
├── Knowledge/
│   ├── Architecture/
│   ├── Composants/
│   ├── Sécurité/
│   ├── Syntheses/
│   │   └── by-agent/
│   └── documents sources préservés
├── Operational-Memory/
│   ├── PROJECT_STATE.md
│   ├── DECISIONS.md
│   ├── TASKS.md
│   ├── BLOCKERS.md
│   └── sources/
└── _meta/
    ├── SOURCE_INVENTORY.md
    └── MIGRATION_REPORT.md
```

## Règles de classification

1. Une archive historique n'est jamais modifiée.
2. Une synthèse d'agent n'est pas une preuve de l'état actuel du code.
3. Une tâche non exécutée ne doit pas être signalée comme réussie.
4. Un fichier exactement identique par SHA-256 n'est conservé qu'une fois dans la cible, mais toutes les provenances sont consignées dans `_meta/SOURCE_INVENTORY.md`.
5. Une version divergente est conservée explicitement et avec son origine.
6. Les liens internes sont relatifs. Les liens absolus `file://...` doivent être considérés comme douteux jusqu'à vérification.
7. Aucun secret, token, mot de passe, clé privée, cookie, URL signée ou donnée sensible n'est conservé.
8. Les copies conservent les noms et métadonnées disponibles.

## Distinction entre les trois niveaux

| Niveau | Rôle | Autorité |
|---|---|---|
| Archives | Trace historique fidèle | Evidence de ce qui a été tenté |
| Knowledge | Synthèse et organisation | Navigation et contexte |
| Operational-Memory | État et actions | Direction immediate pour un agent |

Si une information de Knowledge ou d'Archive contredit le dépôt réel, le dépôt réel l'emporte. Il faut alors mettre à jour Operational-Memory et Knowledge, en conservant l'ancienne information si elle reste pertinente.

## Mise à jour

Avant toute mise à jour importante :

1. vérifier l'état Git ;
2. identifier le document source concerné ;
3. conserver l'ancienne version si elle reste pertinente ;
4. comparer les empreintes SHA-256 ;
5. mettre à jour `INDEX.md` si la structure change ;
6. mettre à jour `_meta/MIGRATION_REPORT.md` ou un rapport de modification équivalent ;
7. ne jamais supprimer un document uniquement parce qu'il est ancien.

## Sources reconnues

- `/home/fatsio/AI/Ethan/daena` : source locale intégrée et convertie en copies sous `Archives/` et `_meta/`.
- `/home/fatsio/ethan-knowledge` : source externe, dont seules les versions uniques et divergentes ont été importées.
- `/home/fatsio/AI/Ethan/docs/memory` : mémoire opérationnelle source, copiée dans `Operational-Memory/sources/docs-memory/`.
- `docs/adr`, `docs/audit`, `docs/plans` : documentation projet restant la référence applicative directe.

## Règles d'exploitation pour un agent

Un agent doit :

1. consulter Operational-Memory en premier ;
2. vérifier les faits importants dans le dépôt avant d'agir ;
3. utiliser Knowledge pour retrouver architecture, conventions et historique technique ;
4. utiliser Archives pour comprendre des échanges passés ;
5. ne jamais supposer l'état courant uniquement à partir d'une synthèse d'agent ;
6. ne pas exécuter d'action destructive sans autorisation humaine ;
7. citer la source et la date quand un statut est repris dans un nouveau document.

## Maintenances effectuées dans cette migration

- 84 doublons exacts entre les deux sources ont été consolidés sans copie supplémentaire.
- Quatre versions divergentes ont été conservées avec des noms explicites.
- Six éléments uniques ont été conservés.
- L'archive unifiée Cline et ses fragments ont été conservés simultanément.
- Les sources originales ont été laissées intactes.
