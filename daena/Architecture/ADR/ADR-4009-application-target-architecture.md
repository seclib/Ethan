# ADR-4009 — Architecture cible des applications indépendantes

Date : 2026-11-04
Statut : PROPOSED
Issue / contexte : mission 4/6, architecture cible ODIN / Frames / Quantar.

## Contexte

ETHAN déjà intègre ODIN, Frames et Quantar via des manifestes, des services dédiés et des mécanismes de permission. Les trois applications restent technologiquement indépendantes.

## Décision

Définir une architecture cible où :

- ETHAN Core reste source de vérité ;
- HROT reste autorité des permissions ;
- ODIN garde son contrôleur Docker indépendant ;
- Frames et le runtime autonome de Quantar peuvent utiliser ComposeService ;
- Quantar garde son mode one-shot et sa réconciliation ;
- Python reste dominant pour l'IA et les agents ;
- Rust reste spécialisé et subordonné à une façade ;
- TypeScript reste réservé aux interfaces ;
- les capacités applicatives sont validées avant d'être considérées comme opérationnelles.

## Conséquences

- contrats applicatifs documentés et réutilisables ;
- frontières de confiance explicites ;
- pas de contrôleur universel imposé ;
- pas de migration de langage forcée ;
- architecture hybride conservée et façades explicites.

## Références

- `Obsidian/Architecture/Applications/APP_TECHNICAL_CARTOGRAPHY.md`
- `Obsidian/Architecture/Applications/APP_INTEGRATION_MAP.md`
- `Obsidian/Architecture/Applications/APP_ARCHITECTURE_DECISIONS.md`
- `Obsidian/Architecture/Applications/ETHAN_APPLICATION_TARGET_ARCHITECTURE.md`
- `Obsidian/Architecture/Rust-Python-Migration/ADR-H001-hybrid-boundaries.md`
