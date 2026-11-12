"""Archives des tests `openjarvis` — non collectés.

Ces fichiers testent le CLI historique `openjarvis` (framework Click, Runtime
legacy), dont le code n'existe plus dans ETHAN. Voir `README.md` du dossier
pour la justification détaillée.

`collect_ignore_glob` empêche pytest de les collecter : sans cela, la suite
CLI resterait inexécutable (erreurs d'import `No module named 'openjarvis'`).
Les fichiers sont conservés intacts comme référence du contrat historique.
"""

collect_ignore_glob = ["*"]
