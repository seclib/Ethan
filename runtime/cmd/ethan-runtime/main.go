package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/seclib/Ethan/runtime/internal/docker"
	"github.com/seclib/Ethan/runtime/internal/socket"
)

func main() {
	// Parse flags
	configPath := flag.String("config", "/etc/ethan/runtime.yaml", "Path to config file")
	flag.Parse()

	// Print banner
	fmt.Println("◆ ETHAN Runtime")
	fmt.Println("  Docker Controller")
	fmt.Println()

	// Use config path
	_ = *configPath

	// Initialize Docker controller
	fmt.Println("Initializing Docker controller...")
	controller, err := docker.NewController()
	if err != nil {
		log.Fatalf("✗ Failed to initialize Docker controller: %v", err)
	}
	fmt.Println("  ✓ Docker controller ready")

	// Initialize Docker handler
	dockerHandler := docker.NewDockerHandler(controller)

	// Create socket server
	socketPath := "/run/ethan/runtime.sock"
	server := socket.NewServer(socketPath, dockerHandler)

	// Start socket server in background
	go func() {
		if err := server.Start(); err != nil {
			log.Fatalf("✗ Socket server failed: %v", err)
		}
	}()

	fmt.Println("  ✓ Socket server listening on /run/ethan/runtime.sock")
	fmt.Println()

	// Print status
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("✓ Runtime is ready")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println()
	fmt.Println("Communication:")
	fmt.Println("  Socket: /run/ethan/runtime.sock")
	fmt.Println("  HTTP:   http://localhost:8080")
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  services.start  - Start services")
	fmt.Println("  services.stop   - Stop services")
	fmt.Println("  services.status - Get status")
	fmt.Println("  services.logs   - Get logs")
	fmt.Println()
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println()

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Block until signal received
	<-sigChan

	fmt.Println()
	fmt.Println("◆ Shutting down...")

	// Stop socket server
	server.Stop()

	fmt.Println("✓ Runtime stopped")
}