# Spécification — Manifeste d'application ETHAN (MEM-014 Phase 1)

## Format

Le manifeste d'une application indépendante est un document **YAML versionné**.
La validation formelle est assurée par un **JSON Schema** (`Obsidian/Engineering/Specs/application-manifest.schema.json`)
et par le service Python `ContractValidator`.

Les manifestes déclarent ; ils n'accordent aucune permission.

## Identité

L'identité est portée par le bloc `identity`, distincte de toute instance :

- `app_id` : identifiant stable de l'application.
- `instance_id` : identifiant de l'instance déployée.
- `name` : nom lisible.
- `version` : version sémantique de l'application.
- `contract_version` : version du contrat ETHAN ciblée.
- `publisher` : propriétaire de l'application.
- `manifest_version` : version du manifeste.

## Champs racine autorisés

- `identity` (obligatoire)
- `capabilities`
- `dependencies`
- `compatibility`
- `incompatibilities`
- `interfaces`
- `permissions`
- `provenance`
- `metadata`

Tout autre champ racine est rejeté comme champ non autorisé.

## Règles structurales

- Les capacités déclarées sont des noms ou objets `{name, description, declared_by}`.
- Les dépendances portent `name`, `version` et `required`.
- Les interfaces portent `kind` et `entrypoint`.
- La provenance porte au minimum `source` ; le digest, lorsqu'il est présent, est un SHA-256 hexadécimal de 64 caractères.
- Les manifestes ne contiennent ni clé privée ni secret.

## Compatibilité

`contract_version` doit appartenir à l'ensemble des versions prises en charge par ETHAN
(`1.0.0` pour cette phase). Une version syntaxiquement valide mais non prise en charge
produit le statut `incompatible`, jamais `valid`.

## Validation

Statuts explicites :

- `valid` : aucune erreur.
- `invalid` : structure ou valeur invalide.
- `incomplete` : champ requis absent.
- `incompatible` : version du contrat non prise en charge.

La validation structurelle n'équivaut pas à une conformité complète de l'application.
