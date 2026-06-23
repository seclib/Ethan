package bus

import (
	"encoding/json"
	"fmt"
	"time"

	"ethan/kernel/types"
)

// EventBus wraps NATS connection for event pub/sub.
type EventBus struct {
	subscribers map[string][]func([]byte)
}

// Connect creates a new EventBus connection.
func Connect(addr string) (*EventBus, error) {
	return &EventBus{subscribers: make(map[string][]func([]byte))}, nil
}

// Publish sends bytes to a subject.
func (b *EventBus) Publish(subject string, data []byte) {
	if subs, ok := b.subscribers[subject]; ok {
		for _, handler := range subs {
			handler(data)
		}
	}
}

// Subscribe registers a handler for a subject pattern.
func (b *EventBus) Subscribe(pattern string, handler func([]byte)) (int, error) {
	b.subscribers[pattern] = append(b.subscribers[pattern], handler)
	return len(b.subscribers[pattern]), nil
}

// Close cleans up the bus.
func (b *EventBus) Close() {
	b.subscribers = nil
}

// ParseEvent deserializes a JSON message into an Event.
func ParseEvent(data []byte) types.Event {
	var ev types.Event
	if err := json.Unmarshal(data, &ev); err != nil {
		ev = types.NewEvent("parse.error", "bus", map[string]any{"error": err.Error()}, nil)
	}
	return ev
}

// MustConnect panics on failure.
func MustConnect(addr string) *EventBus {
	nc, err := Connect(addr)
	if err != nil {
		panic(fmt.Sprintf("bus connect: %v", err))
	}
	return nc
}