package api

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Server HTTP API server (fallback)
type Server struct {
	port    string
	handler CommandHandler
}

// CommandHandler interface for handling commands
type CommandHandler interface {
	HandleCommand(cmd *Command) *Response
}

// Command represents a client request
type Command struct {
	Type       string                 `json:"type"`
	SessionID  string                 `json:"session_id"`
	Timestamp  string                 `json:"timestamp,omitempty"`
	Payload    map[string]interface{} `json:"payload"`
}

// Response represents a server response
type Response struct {
	Type       string                 `json:"type"`
	SessionID  string                 `json:"session_id"`
	Payload    map[string]interface{} `json:"payload"`
}

// NewServer creates a new HTTP API server
func NewServer(port string, handler CommandHandler) *Server {
	return &Server{
		port:    port,
		handler: handler,
	}
}

// Start starts the HTTP server
func (s *Server) Start() error {
	// Register handlers
	http.HandleFunc("/", s.handleRequest)
	http.HandleFunc("/stream", s.handleStream)
	
	// Start server
	addr := "127.0.0.1:" + s.port
	fmt.Printf("✓ HTTP server listening on %s\n", addr)
	
	return http.ListenAndServe(addr, nil)
}

// handleRequest handles synchronous requests
func (s *Server) handleRequest(w http.ResponseWriter, r *http.Request) {
	// Only allow POST
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Set headers
	w.Header().Set("Content-Type", "application/json")
	
	// Decode command
	var cmd Command
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		s.sendError(w, cmd.SessionID, "INVALID_REQUEST", "Malformed JSON", err.Error())
		return
	}
	
	// Handle command
	resp := s.handler.HandleCommand(&cmd)
	
	// Send response
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		fmt.Printf("✗ Failed to send response: %v\n", err)
	}
}

// handleStream handles streaming requests (SSE)
func (s *Server) handleStream(w http.ResponseWriter, r *http.Request) {
	// Only allow POST
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	
	// Set SSE headers
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	
	// Decode command
	var cmd Command
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		fmt.Fprintf(w, "data: %s\n\n", json.MustMarshal(map[string]interface{}{
			"type": "error",
			"payload": map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": "Malformed JSON",
				"details": err.Error(),
			},
		}))
		return
	}
	
	// Handle command (streaming)
	// Note: For streaming, the handler should return multiple responses
	// This is a simplified version
	resp := s.handler.HandleCommand(&cmd)
	
	// Send response as SSE
	data, _ := json.Marshal(resp)
	fmt.Fprintf(w, "data: %s\n\n", data)
	
	// Flush
	if flusher, ok := w.(http.Flusher); ok {
		flusher.Flush()
	}
}

// sendError sends an error response
func (s *Server) sendError(w http.ResponseWriter, sessionID, code, message, details string) {
	resp := &Response{
		Type:      "error",
		SessionID: sessionID,
		Payload: map[string]interface{}{
			"code":    code,
			"message": message,
			"details": details,
		},
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	json.NewEncoder(w).Encode(resp)
}

// HealthCheck handles health check requests
func (s *Server) HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status": "ok",
		"time":   time.Now().Unix(),
	})
}