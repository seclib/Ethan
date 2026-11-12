# 07 — Root Causes

## Causes probables principales

1. Multiples statuts d’application (`registered`, `available`, `lifecycle`) pouvant diverger de Docker réel.
2. Plugin installation dépendante de permissions backend et HROT, avec formats/stdato possible mismatch.
3. `available` traité comme opérationnel dans des menus sans vérification conteneur.
4. `capabilities` router hétérogène : agglomère plusieurs sous-domaines.
5. Provider Gateway HROT non intégré au worker, cause l'erreur OpenAI dans Quantar.
6. Provider catalog Ollama supporté, mais modèles catalogués non installés.

## Preuves

- Discovery state explicit: discovery crée DECLARED seulement (fichier inspecté).
- Application registry distinct lifecycle state.
- Plugin router permission and guard code inspecté.
- Gateway in-process and non-integrated confirmed by docs/tests.
