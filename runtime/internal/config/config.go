package config

import (
	"fmt"
	"os"
	"time"
)

// Config holds runtime configuration
type Config struct {
	LogLevel    Level
	SocketPath  string
	HTTPPort    string
	Timeout     time.Duration
	PollInterval time.Duration
}

// Level represents log severity
type Level int

const (
	DebugLevel Level = iota
	InfoLevel
	WarnLevel
	ErrorLevel
)

// Load reads configuration from file
func Load(path string) *Config {
	// Defaults
	cfg := &Config{
		LogLevel:     InfoLevel,
		SocketPath:   "/run/ethan/runtime.sock",
		HTTPPort:     ":8002",
		Timeout:      30 * time.Second,
		PollInterval: 500 * time.Millisecond,
	}

	// Try to load from file
	if data, err := os.ReadFile(path); err == nil {
		// Simple YAML parsing (in production, use a proper YAML library)
		content := string(data)
		cfg.parse(content)
	}

	return cfg
}

// parse extracts config from YAML (simplified)
func (c *Config) parse(content string) {
	// In production, use gopkg.in/yaml.v2
	// For now, use defaults
}

// String returns config as string
func (c *Config) String() string {
	return fmt.Sprintf("Config{LogLevel: %d, SocketPath: %s, HTTPPort: %s, Timeout: %v}",
		c.LogLevel, c.SocketPath, c.HTTPPort, c.Timeout)
}