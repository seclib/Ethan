package socket

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"sync"
	"time"
)

// Server Unix socket server
type Server struct {
	socketPath string
	handler    CommandHandler
	mu         sync.Mutex
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

// NewServer creates a new Unix socket server
func NewServer(socketPath string, handler CommandHandler) *Server {
	return &Server{
		socketPath: socketPath,
		handler:    handler,
	}
}

// Start starts the socket server
func (s *Server) Start() error {
	// Remove existing socket
	os.Remove(s.socketPath)
	
	// Create socket
	listener, err := net.Listen("unix", s.socketPath)
	if err != nil {
		return fmt.Errorf("failed to create socket: %w", err)
	}
	defer listener.Close()
	
	// Set permissions (0660 - owner and group can read/write)
	os.Chmod(s.socketPath, 0660)
	
	fmt.Printf("✓ Socket server listening on %s\n", s.socketPath)
	
	// Accept connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			fmt.Printf("✗ Accept error: %v\n", err)
			continue
		}
		
		go s.handleConnection(conn)
	}
}

// handleConnection handles a single client connection
func (s *Server) handleConnection(conn net.Conn) {
	defer conn.Close()
	
	// Set read timeout
	conn.SetReadDeadline(time.Now().Add(30 * time.Second))
	
	// Decode command
	var cmd Command
	decoder := json.NewDecoder(conn)
	if err := decoder.Decode(&cmd); err != nil {
		s.sendError(conn, cmd.SessionID, "INVALID_REQUEST", "Malformed JSON", err.Error())
		return
	}
	
	// Handle command
	resp := s.handler.HandleCommand(&cmd)
	
	// Send response
	encoder := json.NewEncoder(conn)
	if err := encoder.Encode(resp); err != nil {
		fmt.Printf("✗ Failed to send response: %v\n", err)
	}
}

// sendError sends an error response
func (s *Server) sendError(conn net.Conn, sessionID, code, message, details string) {
	resp := &Response{
		Type:      "error",
		SessionID: sessionID,
		Payload: map[string]interface{}{
			"code":    code,
			"message": message,
			"details": details,
		},
	}
	json.NewEncoder(conn).Encode(resp)
}

// Stop stops the socket server
func (s *Server) Stop() {
	os.Remove(s.socketPath)
}