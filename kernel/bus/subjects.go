package bus

// NATS subject constants matching EVENT_BUS.md specification.
const (
	// Interface subjects (source: cli, api, web, vscode)
	SubjectInterfaceCLI   = "ethan.interface.cli"
	SubjectInterfaceAPI   = "ethan.interface.api"
	SubjectInterfaceWeb   = "ethan.interface.web"
	SubjectInterfaceVSCode = "ethan.interface.vscode"

	// Kernel events
	SubjectKernelRequestCreated = "ethan.kernel.request.created"

	// Registry events
	SubjectRegistryCapabilityRegistered = "ethan.registry.capability.registered"
	SubjectRegistryUpdated              = "ethan.registry.updated"

	// Planner events
	SubjectPlannerPlanCreated = "ethan.planner.plan.created"
	SubjectPlannerPlanFailed  = "ethan.planner.plan.failed"

	// Executor events
	SubjectExecutorTaskAssigned  = "ethan.executor.task.assigned"
	SubjectExecutorTaskCompleted = "ethan.executor.task.completed"
	SubjectExecutorTaskFailed    = "ethan.executor.task.failed"

	// Response subjects
	SubjectResponseOK       = "ethan.response.ok"
	SubjectResponseError    = "ethan.response.error"
	SubjectResponseTimeout  = "ethan.response.timeout"
	SubjectResponseRejected = "ethan.response.rejected"

	// System events
	SubjectSystemBoot     = "ethan.system.boot"
	SubjectSystemShutdown = "ethan.system.shutdown"
	SubjectSystemError    = "ethan.system.error"

	// Error events
	SubjectIngestError = "ethan.ingest.error"
)