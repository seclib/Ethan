# ADR — ETHAN Application Catalog (seclib)

Date : 2026-11-03
Statut : proposé

## Décision

seclib est le catalogue central de références d'applications indépendantes.
Chaque application possède son propre dépôt.
ETHAN découvre, vérifie, enregistre et supervise les applications sans hypothèse de confiance automatique.

## Ordre architectural

seclib → Catalogue → ApplicationIntegrationRegistry → MEM-014 Control Plane.

GitHub reste une provenance possible, pas une automaticité.

HROT reste l'autorité finale pour les permissions.
