package registry

import (
	"fmt"
	"strings"
)

// Capability represents a module's declared ability.
type Capability struct {
	Name        string   `json:"name"`
	Version     string   `json:"version"`
	Module      string   `json:"module"`
	Inputs      []string `json:"inputs"`
	Outputs     []string `json:"outputs"`
	StateReads  []string `json:"state_reads"`
	StateWrites []string `json:"state_writes"`
	Dependencies []string `json:"dependencies"`
	Shared      bool     `json:"shared"`
}

// Validate checks capability constraints.
func (c *Capability) Validate(existing map[string]Capability) error {
	if c.Name == "" {
		return fmt.Errorf("capability name is empty")
	}
	parts := strings.Split(c.Name, ".")
	if len(parts) < 2 {
		return fmt.Errorf("capability name must be namespaced: %s", c.Name)
	}
	if c.Module == "" {
		return fmt.Errorf("capability module is empty for %s", c.Name)
	}

	// Check write conflicts unless shared
	for _, key := range c.StateWrites {
		for other := range existing {
			if other == c.Name {
				continue
	}
			cap := existing[other]
			for _, w := range cap.StateWrites {
				if w == key && !cap.Shared && !c.Shared {
					return fmt.Errorf("state write conflict on %s between %s and %s", key, cap.Module, c.Module)
				}
			}
		}
	}
	return nil
}