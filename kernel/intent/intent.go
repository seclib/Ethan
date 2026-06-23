package intent

import (
	"strings"

	"ethan/kernel/types"
)

// Intent represents a normalized user/caller intent.
type Intent struct {
	Name       string
	Confidence float64
}

// Common intents.
const (
	IntentRun      = "run"
	IntentChat     = "chat"
	IntentStatus   = "status"
	IntentGoal     = "goal"
	IntentTask     = "task"
	IntentMemory   = "memory"
	IntentUnknown  = "unknown"
)

// Engine extracts intent from Event.Type.
type Engine struct{}

// NewEngine creates an IntentEngine.
func NewEngine() *Engine {
	return &Engine{}
}

// Extract maps an event type to an Intent.
func (e *Engine) Extract(ev types.Event) Intent {
	t := strings.ToLower(ev.Type)
	switch {
	case strings.Contains(t, "command.executed"):
		return Intent{Name: IntentRun, Confidence: 1.0}
	case strings.Contains(t, "chat"):
		return Intent{Name: IntentChat, Confidence: 0.9}
	case strings.Contains(t, "status"):
		return Intent{Name: IntentStatus, Confidence: 0.9}
	case strings.Contains(t, "goal"):
		return Intent{Name: IntentGoal, Confidence: 0.9}
	case strings.Contains(t, "task"):
		return Intent{Name: IntentTask, Confidence: 0.9}
	case strings.Contains(t, "memory"):
		return Intent{Name: IntentMemory, Confidence: 0.9}
	default:
		return Intent{Name: IntentUnknown, Confidence: 0.0}
	}
}