package modules

import (
	"context"
	"fmt"
	"log"
	"os/exec"
	"sync"
	"syscall"
	"time"
)

// Manager manages Python worker processes
type Manager struct {
	natsURL  string
	config   map[string]AgentConfig
	modules  map[string]*Module
	mu       sync.RWMutex
}

// AgentConfig represents a module configuration
type AgentConfig struct {
	Enabled   bool   `yaml:"enabled"`
	AutoStart bool   `yaml:"auto_start"`
	Module    string `yaml:"module"`
}

// Module represents a running Python worker
type Module struct {
	Config   AgentConfig
	Cmd      *exec.Cmd
	PID      int
	Status   string
	Restarts int
	LastSeen time.Time
}

// NewManager creates a new module manager
func NewManager(natsURL string, config map[string]AgentConfig) *Manager {
	return &Manager{
		natsURL:  natsURL,
		config:   config,
		modules:  make(map[string]*Module),
	}
}

// StartAll starts all configured modules
func (m *Manager) StartAll(ctx context.Context) error {
	var wg sync.WaitGroup
	errCh := make(chan error, len(m.config))

	for name, cfg := range m.config {
		if !cfg.Enabled {
			log.Printf("⏭️  Module '%s' disabled", name)
			continue
		}

		wg.Add(1)
		go func(name string, cfg AgentConfig) {
			defer wg.Done()
			if err := m.startModule(ctx, name, cfg); err != nil {
				errCh <- fmt.Errorf("module %s: %w", name, err)
			}
		}(name, cfg)
	}

	wg.Wait()
	close(errCh)

	// Collect errors
	var errs []error
	for err := range errCh {
		errs = append(errs, err)
	}

	if len(errs) > 0 {
		return fmt.Errorf("failed to start %d modules: %v", len(errs), errs[0])
	}

	return nil
}

// startModule starts a single Python module
func (m *Manager) startModule(ctx context.Context, name string, cfg AgentConfig) error {
	log.Printf("🚀 Starting module: %s (%s)", name, cfg.Module)

	// Build command: python -m core.agents.executive
	cmd := exec.CommandContext(ctx, "python3", "-m", cfg.Module)
	cmd.Args = append(cmd.Args, "--nats-url", m.natsURL)

	// Start process
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start: %w", err)
	}

	module := &Module{
		Config:   cfg,
		Cmd:      cmd,
		PID:      cmd.Process.Pid,
		Status:   "running",
		LastSeen: time.Now(),
	}

	m.mu.Lock()
	m.modules[name] = module
	m.mu.Unlock()

	log.Printf("✅ Module '%s' started (PID: %d)", name, cmd.Process.Pid)

	// Monitor process in background
	go m.monitorModule(ctx, name, module)

	return nil
}

// monitorModule monitors a module and restarts on failure
func (m *Manager) monitorModule(ctx context.Context, name string, module *Module) {
	backoff := 1 * time.Second
	maxBackoff := 30 * time.Second

	for {
		select {
		case <-ctx.Done():
			return
		}

		// Wait for process to exit
		err := module.Cmd.Wait()

		m.mu.Lock()
		module.Status = "stopped"
		m.mu.Unlock()

		if ctx.Err() != nil {
			log.Printf("🛑 Module '%s' stopped (shutdown)", name)
			return
		}

		log.Printf("⚠️  Module '%s' crashed (PID: %d, error: %v)", name, module.PID, err)
		module.Restarts++

		if module.Restarts >= 5 {
			log.Printf("❌ Module '%s' exceeded max restarts, giving up", name)
			return
		}

		// Exponential backoff
		log.Printf("🔄 Restarting module '%s' in %v (attempt %d/5)", name, backoff, module.Restarts)
		time.Sleep(backoff)
		backoff = min(backoff*2, maxBackoff)

		// Restart
		if err := m.startModule(ctx, name, module.Config); err != nil {
			log.Printf("❌ Failed to restart module '%s': %v", name, err)
			backoff = maxBackoff
		}
	}
}

// StopAll stops all running modules
func (m *Manager) StopAll(ctx context.Context) error {
	m.mu.RLock()
	modules := make([]*Module, 0, len(m.modules))
	for _, mod := range m.modules {
		modules = append(modules, mod)
	}
	m.mu.RUnlock()

	var wg sync.WaitGroup
	for _, mod := range modules {
		wg.Add(1)
		go func(mod *Module) {
			defer wg.Done()
			m.stopModule(ctx, mod)
		}(mod)
	}

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// stopModule stops a single module
func (m *Manager) stopModule(ctx context.Context, module *Module) {
	if module.Cmd == nil || module.Cmd.Process == nil {
		return
	}

	log.Printf("🛑 Stopping module '%s' (PID: %d)", module.Cmd.Process.Pid, module.Cmd.Process.Pid)

	// Try graceful shutdown first
	if err := module.Cmd.Process.Signal(syscall.SIGTERM); err != nil {
		log.Printf("⚠️  Failed to send SIGTERM to module: %v", err)
	}

	// Wait for graceful shutdown
	select {
	case <-ctx.Done():
		// Force kill
		log.Printf("⚡ Force killing module '%s'", module.Cmd.Process.Pid)
		module.Cmd.Process.Kill()
	case <-time.After(5 * time.Second):
		// Force kill after timeout
		log.Printf("⚡ Timeout, force killing module '%s'", module.Cmd.Process.Pid)
		module.Cmd.Process.Kill()
	}
}

// GetStatus returns the status of all modules
func (m *Manager) GetStatus() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	status := make(map[string]interface{})
	for name, mod := range m.modules {
		status[name] = map[string]interface{}{
			"pid":      mod.PID,
			"status":   mod.Status,
			"restarts": mod.Restarts,
			"last_seen": mod.LastSeen.Unix(),
		}
	}

	return status
}

// min returns the minimum of two integers
func min(a, b time.Duration) time.Duration {
	if a < b {
		return a
	}
	return b
}