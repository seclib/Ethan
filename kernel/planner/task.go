package planner

import "time"

// Task represents a unit of work decomposed from a goal.
type Task struct {
	ID          string            `json:"id"`
	GoalID      string            `json:"goal_id"`
	Type        string            `json:"type"`
	Capability  string            `json:"capability"` // required capability name
	Params      map[string]string `json:"params"`
	Status      TaskStatus        `json:"status"`
	Retries     int               `json:"retries"`
	MaxRetries  int               `json:"max_retries"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
}

type TaskStatus string

const (
	TaskStatusPending   TaskStatus = "pending"
	TaskStatusAssigned  TaskStatus = "assigned"
	TaskStatusRunning   TaskStatus = "running"
	TaskStatusCompleted TaskStatus = "completed"
	TaskStatusFailed    TaskStatus = "failed"
)