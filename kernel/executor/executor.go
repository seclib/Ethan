package executor

import (
	"encoding/json"
	"time"

	"ethan/kernel/bus"
	"ethan/kernel/planner"
	"ethan/kernel/types"
)

// TaskResult captures the outcome of a single task execution.
type TaskResult struct {
	TaskID   string
	Status   string // ok | error | timeout | rejected
	Result   map[string]any
	Error    string
	Duration time.Duration
}

// Executor runs ExecutionPlan tasks by invoking capabilities via the bus.
type Executor struct {
	bus *bus.EventBus
}

// NewExecutor creates an Executor.
func NewExecutor(b *bus.EventBus) *Executor {
	return &Executor{bus: b}
}

// Execute runs all tasks in a plan sequentially (simplified).
// Real implementation would batch parallel tasks and respect DependsOn.
func (e *Executor) Execute(plan planner.ExecutionPlan) []TaskResult {
	results := make([]TaskResult, 0, len(plan.Tasks))
	for _, task := range plan.Tasks {
		res := e.runTask(task)
		results = append(results, res)
	}
	return results
}

func (e *Executor) runTask(task planner.Task) TaskResult {
	start := time.Now()
	req := types.NewRequest(
		types.Event{ID: task.ID, Type: task.Type, Source: "executor", Payload: task.Params},
		task.Capability,
		[]string{task.Capability},
		types.RequestContext{SourceInterface: "kernel"},
	)
	data, _ := json.Marshal(req.Event)
	e.bus.Publish("ethan.capability."+task.Capability, data)
	// In real impl, wait for module reply; here return simulated result.
	return TaskResult{
		TaskID:   task.ID,
		Status:   "ok",
		Result:   map[string]any{"accepted": true},
		Duration: time.Since(start),
	}
}
