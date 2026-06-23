package planner

import (
	"fmt"
	"ethan/kernel/registry"
)

// Resolution matches a task to a capability and module.
type Resolution struct {
	Capability registry.Capability
	Module     string
	Available  bool
}

// Resolver queries the registry to find capabilities for tasks.
type Resolver struct {
	registry *registry.Service
}

// NewResolver creates a new resolver.
func NewResolver(reg *registry.Service) *Resolver {
	return &Resolver{registry: reg}
}

// ResolveTask finds the best capability for a task.
func (r *Resolver) ResolveTask(task Task) (*Resolution, error) {
	if task.Capability == "" {
		return nil, fmt.Errorf("task has no capability requirement")
	}

	caps, err := r.registry.Resolve(task.Capability)
	if err != nil {
		return nil, err
	}
	if len(caps) == 0 {
		return nil, fmt.Errorf("no capability found for %s", task.Capability)
	}

	cap := caps[0]
	modules := r.registry.ActiveModules()
	available := false
	for _, mod := range modules {
		if mod == cap.Module {
			available = true
			break
		}
	}

	return &Resolution{
		Capability: cap,
		Module:     cap.Module,
		Available:  available,
	}, nil
}

// ResolveByInput finds capabilities that consume an event type.
func (r *Resolver) ResolveByInput(eventType string) []registry.Capability {
	filter := registry.ByInputFilter(eventType)
	return r.registry.Query(filter)
}

// ResolveByOutput finds capabilities that produce an event type.
func (r *Resolver) ResolveByOutput(eventType string) []registry.Capability {
	filter := registry.ByOutputFilter(eventType)
	return r.registry.Query(filter)
}