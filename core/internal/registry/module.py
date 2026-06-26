"""ModuleRegistry — Gestion centralisée des modules.

Registry capable de :
- Enregistrer et désenregistrer des modules
- Gérer le cycle de vie (start, stop, healthcheck)
- Résoudre des modules par capacité
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.modules.base import Module, ModuleContext, ModuleState
from core.modules.interface import ModuleInterface
from core.bus.interface import EventBus
from core.registry.capability import CapabilityRegistry
from core.modules.capability import Capability

logger = logging.getLogger(__name__)


class ModuleNotFoundError(Exception):
    """Module non trouvé dans le registry."""
    pass


class ModuleStartupError(Exception):
    """Échec au démarrage du module."""
    pass


class ModuleRegistry:
    """Registry des modules ETHAN.

    Gère :
    - L'enregistrement des modules
    - Le démarrage et l'arrêt
    - Les healthchecks
    - La résolution par capacité
    """

    def __init__(
        self,
        bus: EventBus,
        capability_registry: CapabilityRegistry,
    ):
        self._bus = bus
        self._capabilities = capability_registry

        self._modules: dict[str, Module] = {}
        self._configs: dict[str, dict[str, Any]] = {}
        self._health_tasks: dict[str, asyncio.Task] = {}

    # ──────────────────────────────────────────────
    # Registration
    # ──────────────────────────────────────────────

    def register(
        self,
        module: Module,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Enregistre un module dans le registry.

        Args:
            module: Instance du module à enregistrer
            config: Configuration optionnelle du module

        Raises:
            ValueError: Si le module est déjà enregistré
        """
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' already registered")

        self._modules[module.name] = module
        self._configs[module.name] = config or {}

        # Si c'est un ModuleInterface, enregistrer ses capacités
        if isinstance(module, ModuleInterface):
            for capability in module.get_capabilities():
                self._capabilities.register(module.name, capability)

        logger.info("Module registered: %s", module.name)

    def unregister(self, name: str) -> bool:
        """Désenregistre un module.

        Args:
            name: Nom du module à désenregistrer

        Returns:
            True si le module a été trouvé et supprimé
        """
        if name not in self._modules:
            return False

        # Arrêter le healthcheck
        self._stop_healthcheck(name)

        # Désenregistrer les capacités
        self._capabilities.unregister_module(name)

        # Supprimer le module
        del self._modules[name]
        self._configs.pop(name, None)

        logger.info("Module unregistered: %s", name)
        return True

    # ──────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────

    async def start(self, name: str) -> None:
        """Démarre un module enregistré.

        Args:
            name: Nom du module à démarrer

        Raises:
            ModuleNotFoundError: Si le module n'est pas enregistré
            ModuleStartupError: Si le démarche échoue
        """
        module = self._modules.get(name)
        if module is None:
            raise ModuleNotFoundError(f"Module '{name}' not found")

        try:
            context = ModuleContext(
                name=name,
                bus=self._bus,
                config=self._configs.get(name, {}),
            )
            await module.initialize(context)
            logger.info("Module started: %s", name)
        except Exception as e:
            raise ModuleStartupError(f"Failed to start module '{name}': {e}") from e

    async def stop(self, name: str) -> None:
        """Arrête un module.

        Args:
            name: Nom du module à arrêter
        """
        module = self._modules.get(name)
        if module is None:
            return

        self._stop_healthcheck(name)
        await module.shutdown()
        logger.info("Module stopped: %s", name)

    async def start_all(self) -> None:
        """Démarre tous les modules enregistrés."""
        for name in self._modules:
            try:
                await self.start(name)
            except Exception as e:
                logger.error("Failed to start module '%s': %s", name, e)

    async def stop_all(self) -> None:
        """Arrête tous les modules."""
        for name in list(self._modules.keys()):
            await self.stop(name)

    # ──────────────────────────────────────────────
    # Healthcheck
    # ──────────────────────────────────────────────

    def _start_healthcheck(self, name: str, interval: int = 15) -> None:
        """Démarre la boucle de healthcheck pour un module.

        Args:
            name: Nom du module
            interval: Intervalle en secondes entre chaque check
        """

        async def _healthcheck_loop():
            while True:
                try:
                    await asyncio.sleep(interval)
                    module = self._modules.get(name)
                    if module is None:
                        break
                    if isinstance(module, ModuleInterface):
                        status = await module.health_check()
                        if status.get("status") == "unhealthy":
                            logger.warning(
                                "Module '%s' healthcheck: unhealthy", name
                            )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        "Module '%s' healthcheck failed: %s", name, e
                    )

        task = asyncio.create_task(_healthcheck_loop())
        self._health_tasks[name] = task

    def _stop_healthcheck(self, name: str) -> None:
        """Arrête la boucle de healthcheck.

        Args:
            name: Nom du module
        """
        task = self._health_tasks.pop(name, None)
        if task is not None:
            task.cancel()

    # ──────────────────────────────────────────────
    # Query
    # ──────────────────────────────────────────────

    def get(self, name: str) -> Module | None:
        """Récupère un module par son nom.

        Args:
            name: Nom du module

        Returns:
            Le module, ou None si non trouvé
        """
        return self._modules.get(name)

    def get_by_capability(self, capability_name: str) -> list[Module]:
        """Récupère tous les modules qui déclarent une capacité.

        Args:
            capability_name: Nom de la capacité

        Returns:
            Liste des modules possédant cette capacité
        """
        modules = []
        for module_name, module in self._modules.items():
            if isinstance(module, ModuleInterface):
                for cap in module.get_capabilities():
                    if cap.name == capability_name:
                        modules.append(module)
                        break
        return modules

    def list_all(self) -> list[str]:
        """Liste les noms de tous les modules enregistrés.

        Returns:
            Liste des noms de modules
        """
        return list(self._modules.keys())

    def count(self) -> int:
        """Nombre de modules enregistrés.

        Returns:
            Nombre de modules
        """
        return len(self._modules)

    def __contains__(self, name: str) -> bool:
        return name in self._modules

    def __len__(self) -> int:
        return len(self._modules)