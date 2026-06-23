package ingest

import (
	"encoding/json"
	"time"

	"ethan/kernel/bus"
	"ethan/kernel/types"
)

// Ingest validates, normalizes, and enriches inbound events.
type Ingest struct {
	bus *bus.EventBus
}

// NewIngest creates an Ingest processor.
func NewIngest(b *bus.EventBus) *Ingest {
	return &Ingest{bus: b}
}

// Process receives a raw Event, validates, normalizes, and emits it.
func (i *Ingest) Process(ev types.Event) error {
	if ev.Type == "" || ev.Source == "" {
		errorEv := types.NewEvent("ingest.error", "ingest", map[string]any{"reason": "missing_type_or_source"}, map[string]string{"original_id": ev.ID})
		data, _ := json.Marshal(errorEv)
		i.bus.Publish("ethan.ingest.error", data)
		return nil
	}
	if ev.ID == "" {
		ev.ID = time.Now().Format("20060102150405.999999999")
	}
	if ev.Timestamp.IsZero() {
		ev.Timestamp = time.Now()
	}
	if ev.Payload == nil {
		ev.Payload = map[string]any{}
	}
	if ev.Context == nil {
		ev.Context = map[string]string{}
	}
	subject := "ethan.interface." + ev.Source
	data, _ := json.Marshal(ev)
	i.bus.Publish(subject, data)
	return nil
}
