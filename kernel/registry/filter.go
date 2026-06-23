package registry

import "strings"

// Filter matches capabilities based on criteria.
type Filter struct {
	ByName       string
	ByModule     string
	ByInput      string
	ByOutput     string
	ByDependency string
}

// Matches returns true if the capability satisfies the filter.
func (f Filter) Matches(cap Capability) bool {
	if f.ByName != "" && cap.Name != f.ByName {
		return false
	}
	if f.ByModule != "" && cap.Module != f.ByModule {
		return false
	}
	if f.ByInput != "" {
		found := false
		for _, inp := range cap.Inputs {
			if inp == f.ByInput {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	if f.ByOutput != "" {
		found := false
		for _, out := range cap.Outputs {
			if out == f.ByOutput {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	if f.ByDependency != "" {
		found := false
		for _, dep := range cap.Dependencies {
			if dep == f.ByDependency {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}
	return true
}

// ByNameFilter creates a filter for a specific capability name.
func ByNameFilter(name string) Filter {
	return Filter{ByName: name}
}

// ByInputFilter creates a filter for capabilities that consume an event type.
func ByInputFilter(eventType string) Filter {
	return Filter{ByInput: eventType}
}

// ByOutputFilter creates a filter for capabilities that produce an event type.
func ByOutputFilter(eventType string) Filter {
	return Filter{ByOutput: eventType}
}

// ByModuleFilter creates a filter for a specific module.
func ByModuleFilter(module string) Filter {
	return Filter{ByModule: module}
}

// ByDependencyFilter creates a filter for capabilities requiring a dependency.
func ByDependencyFilter(dep string) Filter {
	return Filter{ByDependency: dep}
}