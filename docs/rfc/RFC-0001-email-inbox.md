# RFC-0001 — Email Inbox ETHAN

## Date
2026-08-24

## Statut
✅ **Implémenté** — voir les sections ci-dessous pour l'architecture livrée.

## Résumé
Boîte de réception e-mail unifiée exposée comme capacité Core (lecture,
recherche, brouillons), rendue par une interface WebUI dédiée.

## Origine
Fonctionnalité phare d'Odysseus (emailInbox.js, emailLibrary). Aucun
équivalent HTTP n'existe aujourd'hui dans ETHAN : seul un lecteur
skill (`core/skills/builtin/email_reader.py`) et des connecteurs
(Gmail) existent côté skills.

## Architecture cible
```
core/channels/email/        ← logique métier (IMAP/SMTP, cache, recherche)
interfaces/api/routers/…    ← /v1/email/* (bindings HTTP minces)
interfaces/webui /email     ← UI (liste, lecture, brouillons)
```

## Portée proposée
1. **Core** — `EmailManager` : connexion IMAP/SMTP multi-comptes,
   sync incrémentale, stockage cache dans `core_domain_records`,
   recherche plein-texte, marquage lu/non-lu, brouillons.
2. **API** — GET/POST `/v1/email/messages`, PATCH lu/non-lu,
   POST `/v1/email/drafts`, POST `/v1/email/sync`.
3. **WebUI** — page `/email` : liste groupée par date, panneau de
   lecture, composition. Aucune logique métier côté UI.
4. **Sécurité** — credentials via secret manager (jamais en base ni
   dans les events), RBAC Permission.READ/WRITE sur les routes.

## Hors portée
- Envoi HTML riche, pièces jointes volumineuses (phase 2).

## Dépendances
- Connecteurs Gmail existants (`tests/connectors/test_gmail.py`).
