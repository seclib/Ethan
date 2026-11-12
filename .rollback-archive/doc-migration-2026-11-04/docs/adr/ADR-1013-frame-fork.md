# ADR-1013 — Fork Frame à partir d'HyperFrames

- Statut : Accepted
- Contexte : préparation d'une application indépendante `Frame` sous `examples/frame`, basée sur HyperFrames commit `8b1f88b3c`.
- Décision : conserver HyperFrames comme référentiel externe; `Frame` doit rester une application indépendante et ne pas être fusionnée dans ETHAN Core/Runtime.
- Intégration ETHAN prévue : service externe confiné, lifecycle inspiré d'ODIN, API passerelle, RBAC ETHAN.
- Ne pas : importer les moteurs Frame dans ETHAN, modifier ODIN, publier sans autorisation.
- Tests / preuves : dépôt clone propre; `git fsck --full` sans erreur; historique et licences préservés; README/docs dans Frame mis à jour.
