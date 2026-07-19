# Kernel Go — Performance Layer

## Rôle

Kernel Go haute performance pour :
- Routage d'événements
- Patterns Request/Reply
- Traitement à haut débit

## Interface avec Python

Le kernel Go communique avec le kernel Python via :
- NATS (event bus partagé)
- gRPC (si nécessaire)

## Statut

⚠️ **Non prêt pour la production** — Kernel Python reste principal.

## Compilation

```bash
cd core/kernel-go
go build -o ethan-core main.go
```

## Tests

```bash
go test ./...