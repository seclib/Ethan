# Engineering Principles — Jarvis OS

> Standards d'engineering pour le développement de Jarvis OS.
> Ces principes sont obligatoires pour toute modification du repository.

---

## 1. No Unsafe Changes

### Règle
Ne jamais modifier le système sans :
- Scope clairement défini
- Justification documentée
- Impact minimisé
- Plan de réversibilité

### Application
- Toute PR doit avoir un scope défini dans sa description
- Les changements "au cas où" sont interdits
- Chaque modification doit pouvoir être annulée proprement

---

## 2. Minimal Diff Principle

### Règle
Chaque changement doit être :
- **Minimal** : le plus petit changement possible
- **Localisé** : limité à un module/composant
- **Réversible** : facile à rollback
- **Testable** : validation possible

### Application
- Une PR = un changement logique
- Pas de refactoring dans une PR fonctionnelle
- Pas de changement de style dans une PR logique
- Les modifications cosmétiques sont des PR séparées

```python
# ✅ Bon : changement ciblé
class NewFeature:
    def method(self):
        ...

# ❌ Mauvais : changement + refactoring + style
class NewFeature:  # + renommage de 10 classes + reformatage
    ...
```

---

## 3. RFC-First Development

### Règle
Toute modification significative doit commencer par une RFC.

### Processus
1. **RFC Draft** → Décrire le problème et la solution proposée
2. **Review** → Discussion et feedback
3. **Acceptation** → Validation pour implémentation
4. **Implémentation** → Code + tests + documentation
5. **Validation** → Vérification des critères

### Quand une RFC est nécessaire
- Nouveau service ou composant
- Changement d'architecture
- Nouvelle dépendance majeure
- Modification du déploiement
- Changement d'interface publique

### Quand une RFC n'est PAS nécessaire
- Bug fix simple
- Documentation
- Tests
- Refactoring mineur (validé verbalement)

---

## 4. Security-First Mindset

### Règle
La sécurité est une contrainte, pas une option.

### Principes
- **Moindre privilège** : chaque composant a le minimum de permissions
- **Défense en profondeur** : plusieurs couches de sécurité
- **Fail secure** : en cas d'erreur, le comportement sécurisé est par défaut
- **No secrets in code** : jamais de clés, tokens ou passwords dans le code source
- **Input validation** : toutes les entrées utilisateur sont validées

### Checklist
- [ ] Pas de secrets en dur
- [ ] Input validation présente
- [ ] Permissions minimales
- [ ] Logging des actions sensibles
- [ ] Rate limiting si exposition publique
- [ ] Sandbox pour exécution de code

---

## 5. Upstream Preservation Rules

### Règle
Ethan est l'upstream. Jarvis OS est une surcouche.

### Principes
- **Ne jamais modifier profondément** le code Ethan
- **Préférer les wrappers** aux modifications directes
- **Proposer à l'upstream** les améliorations génériques
- **Documenter les écarts** entre upstream et overlay

### Interdictions
- ❌ Réécriture de modules Ethan
- ❌ Suppression de fonctionnalités upstream
- ❌ Renommage de packages upstream
- ❌ Modification des APIs publiques upstream sans coordination

### Autorisations
- ✅ Extension via plugins
- ✅ Wrappers et adaptateurs
- ✅ Nouvelles fonctionnalités dans `core/` ou `plugins/`
- ✅ Configuration via `.env` ou `configs/`

---

## 6. Documentation as Code

### Règle
La documentation est traitée comme du code :
- Reviewée
- Versionnée
- Testée (liens, exemples)

### Standards
- ADR pour les décisions architecturales
- Docstrings pour toutes les classes/fonctions publiques
- README pour chaque module
- Exemples fonctionnels dans `examples/`

---

## 7. Testability

### Règle
Tout code doit être testable.

### Principes
- **Dependency injection** : pas de singletons globaux (sauf registry)
- **Interfaces** : dépendre des abstractions, pas des implémentations
- **Async ready** : les fonctions bloquantes sont wrappées
- **Mockable** : les services externes sont mockables

---

## Résumé

```
┌─────────────────────────────────────────────────┐
│           Engineering Principles                │
├─────────────────────────────────────────────────┤
│ 1. No Unsafe Changes       ─── Sécurité         │
│ 2. Minimal Diff Principle  ─── Qualité          │
│ 3. RFC-First Development   ─── Gouvernance      │
│ 4. Security-First Mindset  ─── Sécurité         │
│ 5. Upstream Preservation   ─── Architecture     │
│ 6. Documentation as Code   ─── Maintenabilité   │
│ 7. Testability             ─── Qualité          │
└─────────────────────────────────────────────────┘
```

## Compliance

Ces principes sont vérifiés via :
- Code review obligatoire
- CI checks (lint, test, security scan)
- RFC/ADR requirement check
- Architecture review trimestrielle