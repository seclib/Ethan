package registry

import (
	"encoding/json"
	"log"
	"time"

	"github.com/nats-io/nats.go"
)

// NATSHandler manages registry integration with NATS.
type NATSHandler struct {
	service *Service
	nc      *nats.Conn
	subject string
}

// NewNATSHandler subscribes to NATS for module registration events.
func NewNATSHandler(service *Service, nc *nats.Conn) *NATSHandler {
	h := &NATSHandler{
		service: service,
		nc:      nc,
		subject: "kernel.registry.register",
	}
	h.subscribe()
	return h
}

type RegistrationEvent struct {
	Module      string            `json:"module"`
	Capabilities []Capability     `json:"capabilities"`
	Heartbeat   time.Time         `json:"heartbeat"`
}

func (h *NATSHandler) subscribe() {
	_, err := h.nc.Subscribe(h.subject, func(msg *nats.Msg) {
		var ev RegistrationEvent
		if err := json.Unmarshal(msg.Data, &ev); err != nil {
			log.Printf("registry: invalid registration event: %v", err)
			return
		}
		h.handleRegistration(ev)
	})
	if err != nil {
		log.Fatalf("registry: failed to subscribe: %v", err)
	}
	log.Printf("registry: subscribed to %s", h.subject)
}

func (h *NATSHandler) handleRegistration(ev RegistrationEvent) {
	for _, cap := range ev.Capabilities {
		if err := h.service.Register(cap); err != nil {
			log.Printf("registry: rejected %s from %s: %v", cap.Name, ev.Module, err)
			continue
		}
		log.Printf("registry: registered %s v%s from %s", cap.Name, cap.Version, ev.Module)
	}
	h.publishUpdate()
}

func (h *NATSHandler) publishUpdate() {
	// Publish updated capability list
	caps := h.service.AllCapabilities()
	data, _ := json.Marshal(caps)
	h.nc.Publish("kernel.registry.updated", data)
}

// StartHeartbeatMonitor checks module heartbeats periodically.
func (h *NATSHandler) StartHeartbeatMonitor(interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for range ticker.C {
			modules := h.service.ActiveModules()
			for _, mod := range modules {
				log.Printf("registry: module %s active", mod)
			}
		}
	}()
}