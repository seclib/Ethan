# Documentation — Validateur contractuel (MEM-014 Phase 1)

## Entrée

`core.applications.ContractValidator`

Méthodes principales :

- `validate_manifest_data(mapping)`
- `validate_manifest_file(path)`
- `validate(data_or_path)` (alias adaptatif)
- `validate_yaml(payload)`
- `validate_manifest(payload)` (alias)

## Sortie

`ValidationResult` :

- `is_valid` : booléen.
- `status` : `valid`, `invalid`, `incomplete`, `incompatible`.
- `errors` : tuple de messages explicites.
- `warnings` : tuple de messages non bloquants.
- `identity` : identité extraite si possible.

## Sécurité

- Parsing YAML sûr (`yaml.safe_load`).
- Pas d'exécution du contenu.
- Profondeur et taille bornées.
- Détection de matériel secret évident.
- Refus des champs racine non autorisés.

## Extension

Le constructeur accepte un ensemble de versions de contrat prises en charge pour les
environnements de test ou de migration sans modifier ETHAN.
