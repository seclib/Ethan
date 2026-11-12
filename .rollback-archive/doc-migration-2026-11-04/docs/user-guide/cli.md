# CLI ETHAN

Le CLI est une interface officielle d'ETHAN. Il expose les capacités du Core
par son API HTTP et garde localement uniquement les préférences propres au
terminal. La référence des commandes et du contrat de sortie se trouve dans
[`interfaces/cli/README.md`](../../interfaces/cli/README.md) et
[`docs/specs/CLI_CONTRACT.md`](../specs/CLI_CONTRACT.md).

## Installation depuis le dépôt

Le paquet racine du dépôt déclare la commande `ethan`. Sur Debian et les autres
systèmes qui protègent le Python système, utilisez un environnement virtuel :

```bash
git clone <URL_DU_DEPOT> Ethan
cd Ethan
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
ethan --version
```

Tant que l'environnement virtuel est activé, `ethan` fonctionne depuis
n'importe quel répertoire. Le paquet racine inclut aussi le Core et ses
dépendances Python; ce n'est pas encore une distribution minimale du seul CLI.
Le script historique `interfaces/cli/install.sh` installe `ethan-cli` en
référant le chemin du dépôt et ne constitue pas l'installation officielle.
L'audit de production associé documente les écarts de packaging :
[`CLI_PRODUCTION_AUDIT.md`](../audits/CLI_PRODUCTION_AUDIT.md).

### Mise à jour et désinstallation

Depuis le dépôt, avec le même environnement virtuel activé :

```bash
git pull
python -m pip install --upgrade -e .
```

Pour désinstaller la commande et les fichiers Python installés dans cet
environnement :

```bash
python -m pip uninstall Ethan
```

## Quickstart

Le Core local est attendu à `http://localhost:8000` par défaut. Démarrez-le
selon le mode de déploiement choisi, puis utilisez le CLI :

```bash
ethan --help
ethan status
ethan provider list
ethan chat "Résume les capacités d'ETHAN"
```

Les commandes `help`, `version`, `doctor`, `status`, `config`, `auth` et
`logs` sont visibles dans l'aide du CLI. Les commandes métier disponibles
sont celles enregistrées dans `interfaces/cli/commands/` et exposées par
l'API Core. Consultez `ethan <commande>` et le README du CLI pour leurs
arguments actuels.

## Configuration et Core distant

L'URL par défaut peut être remplacée pour un appel avec `--api-url`, ou pour
la session avec `ETHAN_API_URL` (alias accepté : `ETHAN_API`) :

```bash
ethan --api-url https://ethan.example.net status
ETHAN_API_URL=https://ethan.example.net ethan provider list
```

Les préférences et profils du CLI sont stockés sous
`${XDG_CONFIG_HOME:-~/.config}/ethan/`. `ETHAN_CONFIG_DIR` permet de changer
ce répertoire. Les préférences locales se consultent avec `ethan config list`;
les domaines de configuration du Core passent par `ethan config domains`,
`ethan config core-get <domaine>` et `ethan config core-set <domaine> ...`.

Les options globales comprennent `-o, --output human|json`, `-q, --quiet`,
`-v`, `--no-color`, `--profile`, `--timeout`, `--api-url` et `--token`.
L'aide (`ethan --help`) affiche les options acceptées.

## Authentification

```bash
ethan auth login
ethan auth status
ethan auth logout
```

Le JWT local est conservé dans `credentials.json` avec les permissions
`0600`. Pour les scripts, `ETHAN_TOKEN` est préférable à `--token`, qui est
visible dans la liste des processus. Ne placez pas de secrets dans les
arguments de commandes ou dans les fichiers de configuration non protégés.

## Sorties et scripts

Les erreurs et diagnostics sont écrits sur `stderr`; `-o json` réserve
`stdout` au document JSON afin de permettre le piping :

```bash
ethan -o json provider list | jq .
ethan -o json version
```

Les codes de sortie contractuels sont `0` succès, `2` usage, `3`
authentification, `4` autorisation, `5` API indisponible, `6` introuvable,
`7` délai dépassé, `8` conflit, `70` erreur interne et `130` interruption.

## Commandes système contrôlées

`ethan exec` est distinct des commandes ETHAN. Par exemple, `ethan model
list` consulte le catalogue Core, tandis que `ethan exec ollama list` demande
l'exécution de l'outil local Ollama par le Core.

```bash
ethan exec catalogue
ethan exec ollama list --no-wait
ethan exec git status --short
ethan exec operation <operation-id>
ethan exec cancel <operation-id>
```

Le Core n'interprète jamais une chaîne shell : il lance seulement un exécutable
du catalogue avec un `argv` validé. Le catalogue de base autorise uniquement
des formes en lecture seule de `ollama`, `git`, `python`/`python3` et `node`.
Chaque demande est soumise à une approbation humaine explicite. Un
administrateur examine `ethan exec pending`, puis peut décider avec
`ethan exec approve <approval-id>` ou `ethan exec reject <approval-id>`.

L'exécution conserve stdout et stderr séparément, limite la sortie, masque les
motifs de secrets connus, applique un délai maximal de 120 secondes et permet
l'annulation. `Ctrl+C` depuis le CLI demande l'annulation de l'opération; le
Core termine le groupe de processus de l'enfant, afin de ne pas laisser de
sous-processus connu actif.

Le répertoire de travail doit être relatif à `ETHAN_EXEC_ROOT` (par défaut
`/workspace`) et ne peut pas en sortir, y compris par lien symbolique. Le
processus enfant reçoit un environnement minimal sans tokens ni secrets du
serveur et s'exécute sous l'utilisateur effectif réel du service. Si ce
service est root, la capacité refuse toute commande.

Docker figure dans le catalogue à des fins de diagnostic, mais la politique
Core le refuse par défaut. ETHAN ne monte ni ne transmet
`/var/run/docker.sock`; une installation qui donne ce socket au processus API
reste une décision de déploiement externe, que cette capacité ne contourne
pas et ne crée pas.

Cette première version ne diffuse pas les sorties pendant l'exécution : le
CLI récupère l'état de l'opération puis rend les deux flux séparés à la fin.
Les résultats et décisions d'approbation sont inscrits dans l'audit Core.

## Dépannage

- **API indisponible** : vérifier l'URL avec `ethan config list`, puis
  l'état du Core et l'accès réseau. Le CLI retourne le code `5` sur une
  connexion refusée ou une API indisponible.
- **401** : lancer `ethan auth login` ou vérifier `ETHAN_TOKEN`.
- **403** : le compte authentifié ne possède pas l'autorisation demandée.
- **Commande inconnue** : consulter `ethan help`; les commandes d'extension
  dépendent des routes publiées par le Core.
- **Commande absente après installation** : activer le virtualenv dans lequel
  le paquet a été installé et vérifier `command -v ethan`.
- **Installation Debian refusée** : installer dans un virtualenv; ne pas
  forcer pip à modifier le Python géré par le système.

## Architecture

Les commandes résident dans `interfaces/cli/commands/`. Elles appellent la
frontière HTTP partagée `interfaces/cli/core/api.py` et son client
`interfaces/cli/core/client.py`; l'API et le Core restent propriétaires de
l'état métier. Le CLI ne nécessite pas le répertoire du dépôt pour résoudre
`ethan` après installation du paquet, mais ses dépendances de distribution
sont actuellement celles du paquet racine ETHAN.
