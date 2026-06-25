package router

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/nats-io/nats.go"
)

// Router handles event routing between HTTP and NATS
type Router struct {
	natsURL string
	nc      *nats.Conn
	js      nats.JetStreamContext
}

// NewRouter creates a new event router
func NewRouter(natsURL string) (*Router, error) {
	r := &Router{
		natsURL: natsURL,
	}

	// Connect to NATS
	nc, err := nats.Connect(natsURL, nats.Name("kernel-router"))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}

	// Create JetStream context
	js, err := nc.JetStream()
	if err != nil {
		nc.Close()
		return nil, fmt.Errorf("failed to create JetStream context: %w", err)
	}

	r.nc = nc
	r.js = js

	log.Println("🔗 Router connected to NATS")

	return r, nil
}

// HandleChat processes a chat message
func (r *Router) HandleChat(ctx context.Context, text, sessionID, userID string) (map[string]interface{}, error) {
	// Create event
	event := map[string]interface{}{
		"type": "ethan.interface.message",
		"source": "gateway",
		"payload": map[string]interface{}{
			"text":       text,
			"session_id": sessionID,
			"user_id":    userID,
		},
		"timestamp": time.Now().Unix(),
	}

	eventData, err := json.Marshal(event)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal event: %w", err)
	}

	// Publish to NATS
	subject := "ethan.interface.message"
	if err := r.nc.Publish(subject, eventData); err != nil {
		return nil, fmt.Errorf("failed to publish event: %w", err)
	}

	log.Printf("📨 Published chat event: %s", text)

	// For now, return a simple response
	// TODO: Implement request/reply pattern
	return map[string]interface{}{
		"status": "accepted",
		"message": "Message queued for processing",
	}, nil
}

// HandleCommand processes a structured command
func (r *Router) HandleCommand(ctx context.Context, command string, args []string, meta map[string]interface{}) (map[string]interface{}, error) {
	event := map[string]interface{}{
		"type": "ethan.interface.command",
		"source": "gateway",
		"payload": map[string]interface{}{
			"command": command,
			"args":    args,
			"meta":    meta,
		},
		"timestamp": time.Now().Unix(),
	}

	eventData, err := json.Marshal(event)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal event: %w", err)
	}

	subject := "ethan.interface.command"
	if err := r.nc.Publish(subject, eventData); err != nil {
		return nil, fmt.Errorf("failed to publish event: %w", err)
	}

	log.Printf("📨 Published command event: %s", command)

	return map[string]interface{}{
		"status": "accepted",
	}, nil
}

// GetStatus returns system status
func (r *Router) GetStatus() map[string]interface{} {
	return map[string]interface{}{
		"status": "running",
		"nats":   r.nc.IsConnected(),
		"uptime": time.Now().Unix(),
	}
}

// Close closes the NATS connection
func (r *Router) Close() error {
	if r.nc != nil {
		r.nc.Close()
	}
	return nil
}