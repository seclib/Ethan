# Spécification — Découverte de capacités applicatives (MEM-014 Phase 2)

## Principe

La découverte lit des sources locales explicitement configurées et n'exécute aucun manifeste.
Elle expose des capacités en état `declared` uniquement.

## États

- `declared` : capacité déclarée et syntaxiquement observée.
- `verified` : non promu automatiquement pendant la découverte.
- `available` : non déduit de la déclaration.
- `authorized` : objet d'une décision ultérieure, hors de cette phase.

## API Python

Service principal : `ApplicationDiscoveryService(root)`.

Méthodes :

- `discover()` : retourne un `DiscoveryReport`.
- `list_applications()`
- `get_application(app_id, instance_id=None)`
- `list_capabilities(app_id=None, capability=None, state=None)`
- `list_declared_capabilities(app_id=None)`

## Sécurité

- Source explicitement fournie par l'opérateur.
- Traversée de répertoire contrôlée.
- Liens symboliques non autorisés.
- Taille et alias YAML sécurisés selon les limites existantes.
- Aucune valeur secrète n'est exposée.
- Aucune permission n'est accordée et aucune application n'est démarrée.

## Limites

- La découverte n'équivaut ni à la vérification, ni à la disponibilité, ni à l'autorisation.
- Les manifstes invalides restent consultables avec leur statut de validation.
