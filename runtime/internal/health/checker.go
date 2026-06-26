package health

import (
	"fmt"
	"net"
	"os"
	"os/exec"
	"time"

	"github.com/seclib/Ethan/runtime/internal/logger"
	"github.com/seclib/Ethan/runtime/internal/orchestrator"
)

// Checker performs periodic health checks
type Checker struct {
	orch      *orchestrator.Orchestrator
	log       *logger.Logger
	interval  time.Duration
	stopChan  chan struct{}
}

// New creates a new HealthChecker
func New(orch *orchestrator.Orchestrator, log *logger.Logger) *Checker {
	return &Checker{
		orch:     orch,
		log:      log,
		interval: 10 * time.Second,
		stopChan: make(chan struct{}),
	}
}

// Start begins periodic health checks
func (c *Checker) Start() {
	go c.loop()
}

// Stop halts health checks
func (c *Checker) Stop() {
	close(c.stopChan)
}

// loop runs health checks periodically
func (c *Checker) loop() {
	ticker := time.NewTicker(c.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			c.check()
		case <-c.stopChan:
			return
		}
	}
}

// check performs a single health check
func (c *Checker) check() {
	// Check Docker
	if !c.checkDocker() {
		c.log.Warn("Docker is not available")
		return
	}

	// Check socket
	if !c.checkSocket() {
		c.log.Warn("Runtime socket not accessible")
		return
	}

	// Check services
	services, err := c.orch.GetAllServices()
	if err != nil {
		c.log.Error("Failed to get services: %v", err)
		return
	}

	for _, svc := range services {
		if !c.checkService(svc) {
			c.log.Warn("Service unhealthy: %s", svc.Name)
		}
	}
}

// checkDocker verifies Docker is running
func (c *Checker) checkDocker() bool {
	cmd := exec.Command("docker", "info")
	return cmd.Run() == nil
}

// checkSocket verifies the runtime socket exists
func (c *Checker) checkSocket() bool {
	_, err := os.Stat("/run/ethan/runtime.sock")
	return err == nil
}

// checkService checks if a service is healthy
func (c *Checker) checkService(svc *orchestrator.ServiceStatus) bool {
	if svc.Port == 0 {
		return true // No port to check
	}

	// Try TCP connection
	address := fmt.Sprintf("localhost:%d", svc.Port)
	conn, err := net.DialTimeout("tcp", address, 2*time.Second)
	if err != nil {
		return false
	}
	conn.Close()
	return true
}