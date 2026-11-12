"""Synchronisation utilisateurs Open WebUI → ETHAN.

Open WebUI gère ses propres utilisateurs (SQLite). Ce module permet
de les refléter dans ETHAN Core si nécessaire, sans jamais prendre
le pas sur la gestion d'identité Core.
"""