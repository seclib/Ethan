package orchestrator

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/seclib/Ethan/runtime/internal/logger"
)

// State represents runtime state
type State int

const (
	Stopped State = iota
	Starting
	DockerUp
	CoreStart
	PluginStart
	Running
	ServiceDown
	ServiceRestart
	FullRestart
	Stopping
	Error
)

// ServiceStatus represents a service status
type ServiceStatus struct {
	Name     string
	State    string
	Health   string
	Port     int
	Uptime   time.Duration
}

// HealthStatus represents overall health
type HealthStatus struct {
	Healthy bool
	Services []*ServiceStatus
}

// Orchestrator manages Docker Compose and services
type Orchestrator struct {
	cfg      *Config
	log      *logger.Logger
	state    State
	services map[string]*ServiceStatus
	mu       sync.RWMutex
}

// Config for orchestrator
type Config struct {
	ComposeFile string
	Timeout     time.Duration
}

// New creates a new Orchestrator
func New(cfg *Config, log *logger.Logger) *Orchestrator {
	return &Orchestrator{
		cfg:      cfg,
		log:      log,
		state:    Stopped,
		services: make(map[string]*ServiceStatus),
	}
}

// Start starts all services
func (o *Orchestrator) Start() error {
	o.mu.Lock()
	o.state = Starting
	o.mu.Unlock()

	o.log.Info("Starting services...")

	// Start Docker Compose
	if err := o.startDocker(); err != nil {
		o.setState(Error)
		return fmt.Errorf("failed to start Docker: %w", err)
	}

	o.setState(Running)
	o.log.Info("All services started")
	return nil
}

// Stop stops all services
func (o *Orchestrator) Stop() error {
	o.mu.Lock()
	o.state = Stopping
	o.mu.Unlock()

	o.log.Info("Stopping services...")

	// Stop Docker Compose
	if err := o.stopDocker(); err != nil {
		o.log.Error("Failed to stop Docker: %v", err)
	}

	o.setState(Stopped)
	o.log.Info("All services stopped")
	return nil
}

// Restart restarts all services
func (o *Orchestrator) Restart() error {
	if err := o.Stop(); err != nil {
		return err
	}
	time.Sleep(1 * time.Second)
	return o.Start()
}

// GetState returns current state
func (o *Orchestrator) GetState() State {
	o.mu.RLock()
	defer o.mu.RUnlock()
	return o.state
}

// setState sets the current state (must be called with lock held)
func (o *Orchestrator) setState(s State) {
	o.mu.Lock()
	o.state = s
	o.mu.Unlock()
}

// startDocker runs docker compose up
func (o *Orchestrator) startDocker() error {
	o.log.Info("Running: docker compose -f %s up -d", o.cfg.ComposeFile)

	cmd := exec.Command("docker", "compose", "-f", o.cfg.ComposeFile, "up", "-d")
	cmd.Dir = "/usr/share/ethan/compose"

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("docker compose up failed: %w\nOutput: %s", err, string(output))
	}

	o.log.Info("Docker Compose started")
	return nil
}

// stopDocker runs docker compose down
func (o *Orchestrator) stopDocker() error {
	o.log.Info("Running: docker compose -f %s down", o.cfg.ComposeFile)

	cmd := exec.Command("docker", "compose", "-f", o.cfg.ComposeFile, "down")
	cmd.Dir = "/usr/share/ethan/compose"

	output, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("docker compose down failed: %w\nOutput: %s", err, string(output))
	}

	o.log.Info("Docker Compose stopped")
	return nil
}

// IsHealthy checks if all services are healthy
func (o *Orchestrator) IsHealthy() bool {
	o.mu.RLock()
	defer o.mu.RUnlock()
	return o.state == Running
}

// GetHealthStatus returns health status
func (o *Orchestrator) GetHealthStatus() *HealthStatus {
	o.mu.RLock()
	defer o.mu.RUnlock()

	services := make([]*ServiceStatus, 0, len(o.services))
	for _, s := range o.services {
		services = append(services, s)
	}

	return &HealthStatus{
		Healthy:  o.state == Running,
		Services: services,
	}
}

// GetServiceStatus returns status of a specific service
func (o *Orchestrator) GetServiceStatus(name string) (*ServiceStatus, error) {
	o.mu.RLock()
	defer o.mu.RUnlock()

	s, ok := o.services[name]
	if !ok {
		return nil, fmt.Errorf("service not found: %s", name)
	}
	return s, nil
}

// GetAllServices returns all service statuses
func (o *Orchestrator) GetAllServices() ([]*ServiceStatus, error) {
	o.mu.RLock()
	defer o.mu.RUnlock()

	services := make([]*ServiceStatus, 0, len(o.services))
	for _, s := range o.services {
		services = append(services, s)
	}
	return services, nil
}

// StartService starts a specific service
func (o *Orchestrator) StartService(name string) error {
	o.log.Info("Starting service: %s", name)
	// Implementation depends on service type
	return nil
}

// StopService stops a specific service
func (o *Orchestrator) StopService(name string) error {
	o.log.Info("Stopping service: %s", name)
	// Implementation depends on service type
	return nil
}

// RestartService restarts a specific service
func (o *Orchestrator) RestartService(name string) error {
	o.log.Info("Restarting service: %s", name)
	// Implementation depends on service type
	return nil
}

// checkDocker checks if Docker is available
func checkDocker() bool {
	cmd := exec.Command("docker", "info")
	return cmd.Run() == nil
}

// getDockerVersion returns Docker version
func getDockerVersion() (string, error) {
	cmd := exec.Command("docker", "version", "--format", "{{.Server.Version}}")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

// getComposeVersion returns Docker Compose version
func getComposeVersion() (string, error) {
	cmd := exec.Command("docker", "compose", "version", "--short")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

// getDiskSpace returns available disk space
func getDiskSpace() (string, error) {
	if runtime.GOOS == "windows" {
		return "N/A", nil
	}
	cmd := exec.Command("df", "-h", "/var/lib/ethan")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	scanner := bufio.NewScanner(strings.NewReader(string(output)))
	if scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) >= 4 {
			return fields[3] + " available", nil
		}
	}
	return "unknown", nil
}

// getMemory returns available memory
func getMemory() (string, error) {
	if runtime.GOOS == "windows" {
		return "N/A", nil
	}
	cmd := exec.Command("free", "-h")
	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	scanner := bufio.NewScanner(strings.NewReader(string(output)))
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "Mem:") {
			fields := strings.Fields(line)
			if len(fields) >= 4 {
				return fields[3] + " available", nil
			}
		}
	}
	return "unknown", nil
}

// getProcessInfo returns process info
func getProcessInfo(pid int) (string, error) {
	if pid <= 0 {
		return "not running", nil
	}
	process, err := os.FindProcess(pid)
	if err != nil {
		return "", err
	}
	// Send signal 0 to check if process exists
	err = process.Signal(os.Signal(syscall.Signal(0)))
	if err != nil {
		return "not running", nil
	}
	return fmt.Sprintf("PID %d", pid), nil
}