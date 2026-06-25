package resolver

import (
	"ethan/kernel/registry"
	"ethan/kernel/types"
)

// Resolver matches Requests to Capabilities and Modules.
type Resolver struct {
	registry *registry.Service
}

// NewResolver creates a Resolver.
func NewResolver(reg *registry.Service) *Resolver {
	return &Resolver{registry: reg}
}

// Resolve maps a Request to the best matching Capability.
func (r *Resolver) Resolve(req types.Request) (*registry.Capability, error) {
	if len(req.RequiredCapabilities) == 0 {
		return nil, nil
	}
	name := req.RequiredCapabilities[0]
	caps, err := r.registry.Resolve(name)
	if err != nil {
		return nil, err
	}
	if len(caps) == 0 {
		return nil, nil
	}
	return &caps[0], nil
}