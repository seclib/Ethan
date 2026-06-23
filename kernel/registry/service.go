package registry

import (
	"fmt"
	"sync"
)

// Service is the capability registry.
type Service struct {
	mu             sync.RWMutex
	capabilities   map[string]Capability
	modules        map[string]string // module name → last heartbeat
	dependencies   map[string]bool
}

// NewService creates a new registry.
func NewService() *Service {
	return &Service{
		capabilities: make(map[string]Capability),
		modules:      make(map[string]string),
		dependencies: make(map[string]bool),
	}
}

// Register adds a capability after validation.
func (s *Service) Register(cap Capability) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := cap.Validate(s.capabilities); err != nil {
		return err
	}

	// Check dependencies
	for _, dep := range cap.Dependencies {
		if !s.dependencies[dep] {
			return fmt.Errorf("missing dependency: %s for capability %s", dep, cap.Name)
		}
	}

	s.capabilities[cap.Name] = cap
	s.modules[cap.Module] = cap.Module
	return nil
}

// Resolve finds capabilities by name.
func (s *Service) Resolve(name string) ([]Capability, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	cap, ok := s.capabilities[name]
	if !ok {
		return nil, fmt.Errorf("capability not found: %s", name)
	}
	return []Capability{cap}, nil
}

// Query returns capabilities matching the filter.
func (s *Service) Query(filter Filter) []Capability {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []Capability
	for _, cap := range s.capabilities {
		if filter.Matches(cap) {
			result = append(result, cap)
		}
	}
	return result
}

// RegisterDependency declares a system dependency.
func (s *Service) RegisterDependency(name string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.dependencies[name] = true
}

// GetModuleCapabilities returns all capabilities for a module.
func (s *Service) GetModuleCapabilities(module string) []Capability {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var result []Capability
	for _, cap := range s.capabilities {
		if cap.Module == module {
			result = append(result, cap)
		}
	}
	return result
}

// AllCapabilities returns a copy of all capabilities.
func (s *Service) AllCapabilities() []Capability {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]Capability, 0, len(s.capabilities))
	for _, cap := range s.capabilities {
		result = append(result, cap)
	}
	return result
}

// ActiveModules returns currently registered modules.
func (s *Service) ActiveModules() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	modules := make([]string, 0, len(s.modules))
	for m := range s.modules {
		modules = append(modules, m)
	}
	return modules
}