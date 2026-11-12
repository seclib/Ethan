"""Bridge Open WebUI → ETHAN Core.

Ce module fournit l'adaptateur qui traduit les appels API Open WebUI
vers les endpoints ETHAN Core. Open WebUI reste une interface autonome ;
ce bridge ne fait que traduire les requêtes.

Aucune logique métier n'est implémentée ici — seulement du routage HTTP.
"""