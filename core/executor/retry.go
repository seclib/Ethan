package executor

import (
	"encoding/json"
	"math"
	"time"

	"ethan/kernel/bus"
	"ethan/kernel/planner"
	"ethan/kernel/types"
)

// RetryPolicy defines per-capability retry configuration.
type RetryPolicy struct {
	MaxRetries     int
	InitialDelayMs int
	BackoffFactor  float64
	MaxDelayMs     int
}

// DefaultRetryPolicy is used when no policy is specified.
var DefaultRetryPolicy = RetryPolicy{
	MaxRetries:     3,
	InitialDelayMs: 1000,
	BackoffFactor:  2.0,
	MaxDelayMs:     30000,
}

// WaitDuration calculates the delay for a given attempt number.
func (r *RetryPolicy) WaitDuration(attempt int) time.Duration {
	ms := float64(r.InitialDelayMs) * math.Pow(r.BackoffFactor, float64(attempt))
	if ms > float64(r.MaxDelayMs) {
		ms = float64(r.MaxDelayMs)
	}
	return time.Duration(ms) * time.Millisecond
}

// RunTaskWithRetry executes a task with exponential backoff retry.
func (e *Executor) RunTaskWithRetry(task planner.Task, bus *bus.EventBus) TaskResult {
	policy := DefaultRetryPolicy
	for attempt := 0; ; attempt++ {
		result := e.runTask(task)
		if result.Status != "error" || attempt >= policy.MaxRetries {
			return result
		}
		delay := policy.WaitDuration(attempt)
		retryEv := types.NewEvent("executor.task.retrying", "executor", map[string]any{
			"task_id":  task.ID,
			"attempt":  attempt + 1,
			"delay_ms": delay.Milliseconds(),
		}, nil)
		data, _ := json.Marshal(retryEv)
		bus.Publish("ethan.executor.task.retrying", data)
		time.Sleep(delay)
	}
}

// ExecuteParallel runs tasks concurrently using goroutines.
func (e *Executor) ExecuteParallel(tasks []planner.Task) []TaskResult {
	results := make([]TaskResult, len(tasks))
	done := make(chan struct{}, len(tasks))

	for i, task := range tasks {
		go func(idx int, t planner.Task) {
			results[idx] = e.RunTaskWithRetry(t, e.bus)
			done <- struct{}{}
		}(i, task)
	}

	for range tasks {
		<-done
	}
	return results
}