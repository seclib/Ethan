"""Application identity and manifest primitives for ETHAN (MEM-014 Phase 1)."""

from __future__ import annotations

from core.applications.models import (
    CONTRACT_VERSION,
    ETHAN_CONTRACT_VERSION,
    SUPPORTED_CONTRACT_VERSIONS,
    ApplicationCapability,
    ApplicationDependency,
    ApplicationIdentity,
    ApplicationManifest,
    ApplicationProvenance,
    InterfaceDescriptor,
    ValidationError,
    ValidationResult,
    ValidationStatus,
)
from core.applications.validator import ContractValidator
from core.applications.persistence import (
    ApplicationStateStore,
    open_application_state_store,
)
from core.applications.observability import (
    EngineeringMemoryPromotionFilter,
    EventCollector,
    EventOrigin,
    EventStatus,
    IntegrationEvent,
    OBSERVABILITY_SCHEMA_VERSION,
)
from core.applications.catalog import (
    ApplicationCatalog,
    ApplicationCatalogService,
    CatalogEntry,
    CatalogSource,
)
from core.applications.resilience import (

    CancellationToken,
    ErrorKind,
    ApplicationLifecycleManager,
    CircuitBreaker,
    CircuitBreakerConfig,
    IdempotencyRegistry,
    LifecycleState,
    LifecycleTransitionError,
    OperationResult,
    ResilientExecutor,
    RetryPolicy,
    classify_error,
)
from core.applications.hrot_operations import (
    HrotApprovalRequest,
    HrotOperationStatus,
    HrotTrustStore,
    OperationalHrotService,
    SoftwareEncryptedKeyStorage,
    TrustedKeyReference,
)
from core.applications.compliance import (
    ComplianceEngine,
    ComplianceReport,
    ComplianceResult,
    ComplianceStatus,
)
from core.applications.quantar_integration import (
    QUANTAR_CAPABILITIES,
    QUANTAR_MANIFEST_PATH,
    load_quantar_manifest,
    register_quantar_pilot,
)
from core.applications.odin_integration import (
    ODIN_CONTROL_CAPABILITIES,
    load_odin_manifest,
    odin_capability_matrix,
    register_odin_pilot,
)
from core.applications.application_registry import (
    ApplicationIntegrationRegistry,
    ApplicationIntegrationRegistryService,
    ApplicationRecord,
    ApplicationRegistrationState,
    ApplicationRegistry,
    IntegrationRegistry,
)
from core.applications.capabilities import (
    CapabilityDefinition,
    CapabilityDefinitionError,
    CapabilityLifecycleState,
    CapabilityRegistry,
    CapabilityRegistryService,
    CapabilitySensitivity,
)
from core.applications.contracts import (
    ExtensionContract,
    ExtensionContractValidator,
    IntegrationType,
)
from core.applications.capability_contract import (
    ApplicationCapabilityContract,
    ApplicationCapabilityRegistration,
    register_application_capability,
    get_application_capability_contracts,
)
from core.applications.permissions import (
    ApplicationPermissionService,
    AuthorizationDecision,
    AuthorizationDecisionValue,
    HumanAuthority,
    PermissionEvaluationRequest,
    PermissionGrant,
    PermissionManager,
    PermissionRequest,
    PermissionScope,
    PermissionService,
    PermissionState,
    manifest_fingerprint,
)
from core.applications.discovery import (
    ApplicationDiscoveryService,
    CapabilityDiscoveryService,
    CapabilityState,
    DiscoveryConfig,
    DiscoveryReport,
    DiscoveredApplication,
    DiscoveredCapability,
    DiscoveryConflict,
    DiscoveryError,
)

from core.applications.integration_preview import (
    IntegrationPreview,
    IntegrationPreviewService,
    build_integration_preview,
)
from core.applications.integration_approval import (
    IntegrationApprovalRequest,
    IntegrationApprovalDecision,
    IntegrationApprovalService,
    IntegrationApprovalStatus,
)

from core.applications.manifest_repository import (
    ApplicationManifestRepository,
    ApplicationManifestRecord,
)

from core.applications.integration_registration import (
    IntegrationRegistrationResult,
    ApplicationRegistrationService,
)

__all__ = [
    "ApplicationDiscoveryService",
    "CapabilityDiscoveryService",
    "CapabilityState",
    "DiscoveryConfig",
    "DiscoveryReport",
    "DiscoveredApplication",
    "DiscoveredCapability",
    "DiscoveryConflict",
    "DiscoveryError",
    "IntegrationPreview",
    "IntegrationPreviewService",
    "IntegrationApprovalRequest",
    "IntegrationApprovalDecision",
    "IntegrationApprovalService",
    "ApplicationManifestRepository",
    "ApplicationRegistrationService",
    "IntegrationRegistrationResult",
    "IntegrationApprovalStatus",
    "build_integration_preview",
    "CONTRACT_VERSION",
    "ETHAN_CONTRACT_VERSION",
    "SUPPORTED_CONTRACT_VERSIONS",
    "ApplicationCapability",
    "ApplicationDependency",
    "ApplicationIdentity",
    "ApplicationManifest",
    "ApplicationProvenance",
    "ContractValidator",
    "InterfaceDescriptor",
    "ValidationError",
    "ValidationResult",
    "ValidationStatus",
]
