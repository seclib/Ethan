# Data Protection & Anti-Exfiltration — Phase 06

## Objectif

Empêcher qu'ETHAN, un agent, un LLM, un tool ou un MCP puisse **exfiltrer des
données** sans autorisation explicite.

La règle fondamentale :

```
READ LOCAL DATA   ⇏   SEND DATA EXTERNALLY
```

Un accès en lecture local ne confère **jamais** automatiquement un droit de
transmission vers l'extérieur. Les deux capacités sont indépendantes et
doivent être octroyées séparément.

## Séparation des flux

Les quatre flux de données sont **indépendants** :

| Flux | Enum (`DataFlow`) | Autorisation requise |
|---|---|---|
| Lecture locale | `local_read` | Capability `filesystem:read` (Phase 05) |
| Écriture locale | `local_write` | Capability `filesystem:write` (Phase 05) |
| Accès réseau | `network_access` | Capability `network:read/write` (Phase 05) |
| **Transmission externe** | `external_transmission` | **Politique explicite** (`ExfilGuard`) |

La transmission externe est une catégorie d'action **distincte** de l'accès
réseau :

- `ActionCategory.EXTERNAL_TRANSMISSION = "external_transmission"` (types.py)
- capability `external_transmission:send` (capabilities.py)
- règle CORE par défaut : `core.net.transmission` → **DENY** (rules.py)

Ainsi, posséder un accès réseau (ex. `network:read` pour consulter une API)
n'autorise pas à **envoyer** des données locales vers cette API.

## Protections des données sensibles

`SensitiveDataClassifier` (`core/security/data/sensitive.py`) détecte les
catégories suivantes dans un texte **et** dans un chemin de fichier :

| Catégorie | Détection texte | Chemins typiques |
|---|---|---|
| `credentials` | — | `credentials.json`, `client_secret.json` |
| `ssh_private_key` | `BEGIN ... PRIVATE KEY-----` | `~/.ssh/`, `id_rsa`, `id_ed25519` |
| `api_key` | `sk-...`, `AKIA...`, `AIza...`, `sk_live_...` | `~/.aws/credentials`, `.env` |
| `token` | `ghp_...`, `xoxb-...`, JWT `eyJ...` | `~/.config/gh/` |
| `cookie` | `sessionid=...`, `PHPSESSID=...` | — |
| `secret` | `secret=`, `password=`, `api_key=` | `.env`, `vault-token` |
| `password_store` | — | `~/.password-store/`, `keyrings/` |
| `private_config` | — | `~/.kube/config`, `/etc/shadow` |
| `personal_data` | email, carte bancaire | — |

- `scan_text` / `scan_path` → `SensitiveScan` (catégories + occurrences masquées)
- `redact` → remplace chaque secret par `[REDACTED:<kind>]`
- `is_sensitive_path` → true si le chemin pointe vers une zone sensible

## Transmission externe : politique explicite obligatoire

`ExfilGuard` (`core/security/data/exfiltration.py`) est le **point d'entrée
obligatoire** pour toute transmission vers l'extérieur. Aucun tool, plugin ou
MCP ne doit appeler une API externe sans passer par lui.

### Flux d'évaluation

```
Transmission externe demandée
        ↓
ExfilGuard.evaluate(destination, content)
        ↓
Politique explicite existe ?
   Non → DENY (fail-closed CR-4)
   Oui ↓
Scan du contenu (SensitiveDataClassifier)
        ↓
Secrets non couverts par la politique ?
   Oui → DENY (ou REDACTED en mode redact)
   Non ↓
Contenu sensible + require_confirmation ?
   Oui → REQUIRE_CONFIRMATION (humain requis)
   Non ↓
ALLOW
```

### Gestion des politiques

```python
guard = ExfilGuard(redact=False)

# Politique explicite : destination + catégories autorisées à sortir
guard.authorize_transmission(
    "https://api.trusted.example.com/**",
    allowed_kinds={},               # aucun secret autorisé
    granted_by="admin",
    ttl_seconds=3600,               # durée de vie limitée
)

guard.revoke_transmission("https://api.trusted.example.com/**")
```

### Exécution protégée

```python
await guard.transmit(
    "https://api.trusted.example.com/v1/ingest",
    content,
    send_to_api,                    # jamais appelé si DENY
)
```

Le callback n'est **jamais** invoqué si la décision est DENY ou non confirmée.

## Anti prompt-injection structurelle

Le contenu récupéré (fichier, page Web, sortie de tool, mémoire) est traité
comme des **données non fiables** — jamais comme des instructions :

- `sanitize_external_content` retire les blocs `<system>` / `<instruction>` /
  `system:` d'un contenu récupéré.
- **Aucune** "autorisation" contenue dans un contenu ne peut créer, modifier
  ou révoquer une politique (`authorize_transmission` n'est accessible qu'à
  l'administration, pas aux tools/agents/LLM).
- Même si un fichier "ordonne" d'envoyer un secret, l'absence de politique
  explicite → DENY.

Invariant : *le contenu n'est jamais une autorisation* (Constitution, Loi
Fondamentale + PR-2).

## Tests adversariaux

`tests/security/test_data_protection.py` (24 tests) :

| Scénario | Résultat attendu |
|---|---|
| Exfiltration d'API key vers destination autorisée | `DENY` (secret non couvert) |
| Export de clé privée SSH | `DENY` |
| Mode `redact` | secret masqué avant envoi, jamais brut |
| Requête réseau non autorisée | `DENY` (fail-closed) |
| Permission bypass (domaines similaires) | `DENY` |
| Révocation / TTL expiré | `DENY` |
| Prompt injection (`<system>…`) | contenu nettoyé + `DENY` |
| Sortie de tool pseudo-autorisante | ignorée, `DENY`, aucune politique créée |
| `transmit` sur refus | callback **jamais** appelé |
| Sensible sans approbation humaine | `REQUIRE_CONFIRMATION` → refus |
| Audit de chaque évaluation | `total=3, allow=2, deny=1` |

## Verdict

**PASS** si et seulement si les scénarios d'exfiltration sont bloqués **par le
système** (politiques + scan structurel), et non simplement par une instruction
de prompt.

- ✅ Séparation structurelle des 4 flux (catégorie dédiée + capability dédiée)
- ✅ Politique explicite obligatoire (fail-closed sans politique)
- ✅ Scan de contenu sortant (secrets non couverts → bloqués/masqués)
- ✅ Prompt injection sans effet (le contenu ne crée aucune autorisation)
- ✅ Révocation + TTL + audit append-only
- ✅ Callback d'exécution jamais appelé sur refus (non contournable)
