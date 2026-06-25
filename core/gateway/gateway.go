package gateway

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/seclib/Ethan/kernel/router"
	"github.com/gin-gonic/gin"
)

// Server represents the HTTP gateway
type Server struct {
	router     *router.Router
	engine     *gin.Engine
	httpServer *http.Server
}

// NewServer creates a new gateway server
func NewServer(natsURL string, config interface{}) (*Server, error) {
	// Initialize router
	eventRouter, err := router.NewRouter(natsURL)
	if err != nil {
		return nil, fmt.Errorf("failed to create router: %w", err)
	}

	// Set Gin mode
	gin.SetMode(gin.ReleaseMode)
	engine := gin.New()
	engine.Use(gin.Recovery())

	server := &Server{
		router: eventRouter,
		engine: engine,
	}

	// Setup routes
	server.setupRoutes()

	return server, nil
}

// setupRoutes configures HTTP endpoints
func (s *Server) setupRoutes() {
	// Health check
	s.engine.GET("/health", s.healthCheck)

	// API v1
	v1 := s.engine.Group("/api/v1")
	{
		v1.POST("/chat", s.handleChat)
		v1.GET("/status", s.handleStatus)
		v1.POST("/command", s.handleCommand)
	}
}

// healthCheck returns system health status
func (s *Server) healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "healthy",
		"service": "ethan-kernel",
	})
}

// handleChat processes chat messages
func (s *Server) handleChat(c *gin.Context) {
	var req struct {
		Text      string `json:"text" binding:"required"`
		SessionID string `json:"session_id,omitempty"`
		UserID    string `json:"user_id,omitempty"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Route to NATS
	response, err := s.router.HandleChat(c.Request.Context(), req.Text, req.SessionID, req.UserID)
	if err != nil {
		log.Printf("Chat error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process chat"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// handleStatus returns system status
func (s *Server) handleStatus(c *gin.Context) {
	status := s.router.GetStatus()
	c.JSON(http.StatusOK, status)
}

// handleCommand processes structured commands
func (s *Server) handleCommand(c *gin.Context) {
	var req struct {
		Command string                 `json:"command" binding:"required"`
		Args    []string               `json:"args"`
		Meta    map[string]interface{} `json:"meta"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	response, err := s.router.HandleCommand(c.Request.Context(), req.Command, req.Args, req.Meta)
	if err != nil {
		log.Printf("Command error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to execute command"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// Start starts the HTTP server
func (s *Server) Start(addr string) error {
	s.httpServer = &http.Server{
		Addr:         addr,
		Handler:      s.engine,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	log.Printf("🌐 Gateway listening on %s", addr)
	return s.httpServer.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown(ctx context.Context) error {
	if s.httpServer == nil {
		return nil
	}

	log.Println("🔌 Shutting down gateway...")
	return s.httpServer.Shutdown(ctx)
}