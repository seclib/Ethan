"""Stratégies de recherche RAG — abstraction fondée sur les capacités réelles.

ETHAN n'expose que les stratégies mappées sur un chemin de code existant dans
``core/rag/retrieval.py``. Une stratégie est une **configuration** du moteur
de retrieval unique — jamais un second système RAG :

- ``auto``     → comportement historique : sémantique si embeddings réels,
                 sinon recherche par mots-clés (défaut).
- ``keyword``  → recherche textuelle seule (``_textual_retrieve``).
- ``semantic`` → recherche vectorielle seule (cosine / vector store).
- ``hybrid``   → mots-clés + sémantique fusionnés par RRF.

Le reranking n'est **pas** exposé : aucune capacité (cross-encoder, méthode
``rank``/``rerank`` sur un provider LLM) n'existe dans ETHAN à ce jour.

Le choix de l'utilisateur est traduit en configuration technique réelle
(dispatch dans ``RAGRetrieval.retrieve``), persistée globalement
(``rag-config``) ou par collection (``retrieval_strategy``).
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_STRATEGY = "auto"

# Identifiants réels supportés par le moteur de retrieval Core.
_STRATEGY_IDS = ("auto", "keyword", "semantic", "hybrid")


@dataclass(frozen=True)
class RAGStrategy:
    """Description d'une stratégie de recherche réellement implémentée.

    Attributes:
        id: Identifiant technique (valeur persistée en configuration).
        label: Libellé compréhensible pour l'utilisateur (français).
        description: Explication courte de ce que fait réellement la stratégie.
        requires_embeddings: True si la stratégie dépend d'embeddings réels
            (mock/zéros → dégradation documentée vers le chemin textuel).
    """

    id: str
    label: str
    description: str
    requires_embeddings: bool = False


_STRATEGIES: dict[str, RAGStrategy] = {
    "auto": RAGStrategy(
        id="auto",
        label="Automatique (recommandé)",
        description=(
            "Choix automatique : recherche sémantique si les embeddings sont "
            "réels, sinon recherche par mots-clés. Comportement par défaut d'ETHAN."
        ),
    ),
    "keyword": RAGStrategy(
        id="keyword",
        label="Simple — mots-clés",
        description=(
            "Recherche textuelle par présence des mots de la requête. Rapide, "
            "fonctionne sans modèle d'embedding."
        ),
    ),
    "semantic": RAGStrategy(
        id="semantic",
        label="Sémantique",
        description=(
            "Recherche vectorielle sur les embeddings des chunks (similarité "
            "cosinus). Meilleure pour les requêtes reformulées. Nécessite des "
            "embeddings réels ; sinon repli automatique sur les mots-clés."
        ),
        requires_embeddings=True,
    ),
    "hybrid": RAGStrategy(
        id="hybrid",
        label="Hybride (mots-clés + sémantique)",
        description=(
            "Exécute la recherche par mots-clés et la recherche sémantique, "
            "puis fusionne les résultats (filtrage réciproque RRF). Le plus "
            "robuste en pratique."
        ),
    ),
}


def available_strategies() -> list[dict[str, object]]:
    """Stratégies réellement implémentées, pour exposition API/WebUI.

    Ne retourne jamais de stratégie non supportée par le moteur Core.
    """
    return [
        {
            "id": s.id,
            "label": s.label,
            "description": s.description,
            "requires_embeddings": s.requires_embeddings,
        }
        for s in _STRATEGIES.values()
    ]


def get_strategy(strategy_id: str) -> RAGStrategy:
    """Retourne la stratégie demandée (``ValueError`` si inconnue)."""
    candidate = str(strategy_id).strip().lower()
    if candidate not in _STRATEGIES:
        raise ValueError(
            f"Stratégie RAG inconnue : {strategy_id!r} "
            f"(disponibles : {', '.join(_STRATEGIES)})"
        )
    return _STRATEGIES[candidate]


def normalize_strategy(value: str | None) -> str:
    """Valide et normalise un identifiant de stratégie.

    ``None`` ou valeur invalide → défaut global (``auto``). Les identifiants
    inconnus ne lèvent pas : une configuration héritée ou un client tiers ne
    doit jamais casser la recherche — le défaut est fail-safe.
    """
    if not value:
        return DEFAULT_STRATEGY
    candidate = str(value).strip().lower()
    if candidate in _STRATEGY_IDS:
        return candidate
    return DEFAULT_STRATEGY


def validate_strategy(value: str) -> str:
    """Validation stricte pour les entrées utilisateur (API/WebUI).

    Lève ``ValueError`` si la stratégie n'existe pas — l'utilisateur ne doit
    pas pouvoir enregistrer une stratégie non implémentée.
    """
    candidate = str(value).strip().lower()
    if candidate not in _STRATEGY_IDS:
        raise ValueError(
            f"Stratégie RAG inconnue : {value!r} "
            f"(disponibles : {', '.join(_STRATEGY_IDS)})"
        )
    return candidate


def recommend_strategy(has_real_embeddings: bool) -> dict[str, object]:
    """Recommandation de stratégie fondée sur les capacités réelles du moteur.

    La logique de recommandation appartient au Core (les interfaces ne font
    que l'afficher) :

    - embeddings réels   → ``hybrid`` : mots-clés + sémantique fusionnés par
      RRF, la combinaison la plus robuste en pratique ;
    - embeddings mock    → ``auto`` : la voie sémantique se replierait de
      toute façon sur le textuel ; le défaut historique choisit seul le
      meilleur chemin disponible et profitera automatiquement des embeddings
      dès qu'un provider sera configuré.

    ``has_real_embeddings`` est inclus pour que les interfaces puissent
    signaler qu'une stratégie ``requires_embeddings`` choisie explicitement
    se dégradera tant que les embeddings restent mock.
    """
    if has_real_embeddings:
        return {
            "strategy_id": "hybrid",
            "reason": (
                "Embeddings réels disponibles : la recherche hybride combine "
                "mots-clés et sémantique — la plus robuste en pratique."
            ),
            "has_real_embeddings": True,
        }
    return {
        "strategy_id": "auto",
        "reason": (
            "Aucun embedding réel (provider non configuré ou modèle absent) : "
            "la stratégie automatique choisit le meilleur chemin disponible "
            "et basculera vers l'hybride dès que les embeddings seront réels."
        ),
        "has_real_embeddings": False,
    }


__all__ = [
    "DEFAULT_STRATEGY",
    "RAGStrategy",
    "available_strategies",
    "get_strategy",
    "normalize_strategy",
    "recommend_strategy",
    "validate_strategy",
]
