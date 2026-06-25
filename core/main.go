package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/seclib/Ethan/kernel/gateway"
	"github.com/seclib/Ethan/kernel/modules"
)

func main() {
	// Parse flags
	configPath := flag.String("config", "./ethan.yaml", "Path to config file")
	natsURL := flag.String("nats-url", "nats://localhost:4222", "NATS server URL")
	flag.Parse()

	// Load config
	config, err := loadConfig(*configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Create context with cancellation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialize module manager
	moduleManager := modules.NewManager(*natsURL, config)

	// Start all configured modules
	if err := moduleManager.StartAll(ctx); err != nil {
		log.Fatalf("Failed to start modules: %v", err)
	}

	// Initialize HTTP gateway
	gatewayServer, err := gateway.NewServer(*natsURL, config)
	if err != nil {
		log.Fatalf("Failed to create gateway: %v", err)
	}

	// Start gateway in background
	go func() {
		if err := gatewayServer.Start(":8080"); err != nil {
			log.Printf("Gateway error: %v", err)
		}
	}()

	log.Println("✅ ETHAN Kernel started")
	log.Println("   Gateway: http://localhost:8080")
	log.Println("   NATS:    ", *natsURL)
	log.Println("   Modules: ", len(config.Agents))

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	log.Println("\n🛑 Shutting down...")

	// Graceful shutdown
	shutdownCtx, shutdownCancel := context.WithTimeout(ctx, 30*time.Second)
	defer shutdownCancel()

	if err := moduleManager.StopAll(shutdownCtx); err != nil {
		log.Printf("Error during shutdown: %v", err)
	}

	gatewayServer.Shutdown(shutdownCtx)
	log.Println("✅ Shutdown complete")
}

// loadConfig loads configuration from YAML file
func loadConfig(path string) (*Config, error) {
	// TODO: Implement YAML config loading
	// For now, return default config
	return &Config{
		Agents: map[string]AgentConfig{
			"executive": {Enabled: true, AutoStart: true},
			"planner":   {Enabled: true, AutoStart: true},
			"memory":    {Enabled: true, AutoStart: true},
		},
	}, nil
}

// Config represents kernel configuration
type Config struct {
	Agents map[string]AgentConfig `yaml:"agents"`
}

// AgentConfig represents a module configuration
type AgentConfig struct {
	Enabled    bool   `yaml:"enabled"`
	AutoStart  bool   `yaml:"auto_start"`
	ModulePath string `yaml:"module_path"`
}