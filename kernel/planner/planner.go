package planner

import (
	"time"

	"ethan/kernel/registry"
	"ethan/kernel/types"
)

// Task represents a unit of work in a plan.
type Task struct {
	ID          string
	Type        string
	Capability  string
	DependsOn   []string
	Params      map[string]any
	Retries     int
	MaxRetries  int
}

// ExecutionPlan is a set of tasks with dependencies.
type ExecutionPlan struct {
	ID        string
	GoalID    string
	Tasks     []Task
	CreatedAt time.Time
}

// Planner decomposes goals into task DAGs using the capability registry.
type Planner struct {
	reg *registry.Service
}

// NewPlanner creates a Planner.
func NewPlanner(reg *registry.Service) *Planner {
	return &Planner{reg: reg}
}

// Decompose interprets a Request and emits an ExecutionPlan.
func (p *Planner) Decompose(req types.Request) (*ExecutionPlan, error) {
	caps, err := p.reg.Resolve(req.Intent)
	if err != nil || len(caps) == 0 {
		return nil, nil
	}
	cap := caps[0]
	task := Task{
		ID:          req.ID,
		Type:        req.Intent,
		Capability:  cap.Name,
		DependsOn:   []string{},
		Params:      req.Event.Payload,
		MaxRetries:  3,
	}
	return &ExecutionPlan{
		ID:        req.ID,
		GoalID:    req.ID,
		Tasks:     []Task{task},
		CreatedAt: time.Now(),
	}, nil
}