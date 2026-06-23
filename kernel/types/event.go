package types

import (
	"encoding/json"
	"time"
)

// Event represents an immutable event on the bus.
type Event struct {
	ID        string            `json:"id"`
	Type      string            `json:"type"`
	Source    string            `json:"source"`
	Timestamp time.Time         `json:"timestamp"`
	Payload   map[string]any    `json:"payload"`
	Context   map[string]string `json:"context"`
}

// NewEvent creates a new Event with generated ID and timestamp.
func NewEvent(eventType, source string, payload map[string]any, context map[string]string) Event {
	return Event{
		ID:        generateID(),
		Type:      eventType,
		Source:    source,
		Timestamp: time.Now(),
		Payload:   payload,
		Context:   context,
	}
}

func generateID() string {
	return time.Now().Format("20060102150405.999999999")
}

// ToJSON serializes Event to JSON.
func (e Event) ToJSON() ([]byte, error) {
	return json.Marshal(e)
}

// FromJSON deserializes Event from JSON.
func FromJSON(data []byte) (Event, error) {
	var e Event
	err := json.Unmarshal(data, &e)
	return e, err
}