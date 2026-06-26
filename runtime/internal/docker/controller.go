package docker

import (
	"context"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/docker/docker/api/types/container"
	"github.com/docker/docker/client"
)

// Controller manages Docker operations
type Controller struct {
	client *client.Client
}

// NewController creates a new Docker controller
func NewController() (*Controller, error) {
	cli, err := client.NewClientWithOpts(client.FromEnv)
	if err != nil {
		return nil, fmt.Errorf("failed to create Docker client: %w", err)
	}
	
	// Ping Docker daemon
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if _, err := cli.Ping(ctx); err != nil {
		return nil, fmt.Errorf("failed to ping Docker daemon: %w", err)
	}
	
	return &Controller{client: cli}, nil
}

// ServiceStatus represents the status of a service
type ServiceStatus struct {
	Name   string `json:"name"`
	State  string `json:"state"`
	Health string `json:"health"`
	ID     string `json:"id"`
}

// StartService starts a Docker container
func (c *Controller) StartService(serviceName string) error {
	ctx := context.Background()
	
	containerName := fmt.Sprintf("ethan-%s", serviceName)
	
	// Check if container exists
	containers, err := c.client.ContainerList(ctx, container.ListOptions{
		All: true,
	})
	if err != nil {
		return fmt.Errorf("failed to list containers: %w", err)
	}
	
	var containerID string
	for _, ct := range containers {
		for _, name := range ct.Names {
			if name == "/"+containerName {
				containerID = ct.ID
				break
			}
		}
	}
	
	if containerID == "" {
		return fmt.Errorf("container %s not found", containerName)
	}
	
	// Start container
	if err := c.client.ContainerStart(ctx, containerID, container.StartOptions{}); err != nil {
		return fmt.Errorf("failed to start container: %w", err)
	}
	
	return nil
}

// StopService stops a Docker container
func (c *Controller) StopService(serviceName string, timeout int) error {
	ctx := context.Background()
	
	containerName := fmt.Sprintf("ethan-%s", serviceName)
	
	// Get container ID
	containers, err := c.client.ContainerList(ctx, container.ListOptions{
		All: true,
	})
	if err != nil {
		return fmt.Errorf("failed to list containers: %w", err)
	}
	
	var containerID string
	for _, ct := range containers {
		for _, name := range ct.Names {
			if name == "/"+containerName {
				containerID = ct.ID
				break
			}
		}
	}
	
	if containerID == "" {
		return fmt.Errorf("container %s not found", containerName)
	}
	
	// Stop container
	timeoutInt := timeout
	if err := c.client.ContainerStop(ctx, containerID, container.StopOptions{Timeout: &timeoutInt}); err != nil {
		return fmt.Errorf("failed to stop container: %w", err)
	}
	
	return nil
}

// RestartService restarts a Docker container
func (c *Controller) RestartService(serviceName string, timeout int) error {
	ctx := context.Background()
	
	containerName := fmt.Sprintf("ethan-%s", serviceName)
	
	// Get container ID
	containers, err := c.client.ContainerList(ctx, container.ListOptions{
		All: true,
	})
	if err != nil {
		return fmt.Errorf("failed to list containers: %w", err)
	}
	
	var containerID string
	for _, ct := range containers {
		for _, name := range ct.Names {
			if name == "/"+containerName {
				containerID = ct.ID
				break
			}
		}
	}
	
	if containerID == "" {
		return fmt.Errorf("container %s not found", containerName)
	}
	
	// Restart container
	timeoutInt := timeout
	if err := c.client.ContainerRestart(ctx, containerID, container.StopOptions{Timeout: &timeoutInt}); err != nil {
		return fmt.Errorf("failed to restart container: %w", err)
	}
	
	return nil
}

// GetLogs gets logs from a container
func (c *Controller) GetLogs(serviceName string, tail int) (string, error) {
	ctx := context.Background()
	
	containerName := fmt.Sprintf("ethan-%s", serviceName)
	
	// Get container ID
	containers, err := c.client.ContainerList(ctx, container.ListOptions{
		All: true,
	})
	if err != nil {
		return "", fmt.Errorf("failed to list containers: %w", err)
	}
	
	var containerID string
	for _, ct := range containers {
		for _, name := range ct.Names {
			if name == "/"+containerName {
				containerID = ct.ID
				break
			}
		}
	}
	
	if containerID == "" {
		return "", fmt.Errorf("container %s not found", containerName)
	}
	
	// Get logs
	options := container.LogsOptions{
		ShowStdout: true,
		ShowStderr: true,
		Tail:       fmt.Sprintf("%d", tail),
	}
	
	reader, err := c.client.ContainerLogs(ctx, containerID, options)
	if err != nil {
		return "", fmt.Errorf("failed to get logs: %w", err)
	}
	defer reader.Close()
	
	// Read logs
	logBytes, err := io.ReadAll(reader)
	if err != nil {
		return "", fmt.Errorf("failed to read logs: %w", err)
	}
	
	return string(logBytes), nil
}

// GetStatus gets status of all services
func (c *Controller) GetStatus() ([]ServiceStatus, error) {
	ctx := context.Background()
	
	containers, err := c.client.ContainerList(ctx, container.ListOptions{
		All: true,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list containers: %w", err)
	}
	
	var services []ServiceStatus
	for _, ct := range containers {
		// Only include ethan services
		name := strings.TrimPrefix(ct.Names[0], "/")
		if !strings.HasPrefix(name, "ethan-") {
			continue
		}
		
		serviceName := strings.TrimPrefix(name, "ethan-")
		
		status := ServiceStatus{
			Name:   serviceName,
			State:  ct.State,
			Health: "unknown",
			ID:     ct.ID[:12],
		}
		
		// Get health status
		if ct.State == "running" {
			status.Health = "healthy"
		} else if ct.State == "exited" {
			status.Health = "stopped"
		}
		
		services = append(services, status)
	}
	
	return services, nil
}

// StartAllServices starts all ETHAN services in order
func (c *Controller) StartAllServices() error {
	// Level 0: Infrastructure
	infrastructure := []string{"nats", "redis", "postgres"}
	for _, svc := range infrastructure {
		if err := c.StartService(svc); err != nil {
			return fmt.Errorf("failed to start %s: %w", svc, err)
		}
	}
	
	// Wait for infrastructure
	time.Sleep(5 * time.Second)
	
	// Level 1: Runtime
	if err := c.StartService("runtime"); err != nil {
		return fmt.Errorf("failed to start runtime: %w", err)
	}
	
	// Wait for runtime
	time.Sleep(3 * time.Second)
	
	// Level 2: Application
	application := []string{"api", "kernel"}
	for _, svc := range application {
		if err := c.StartService(svc); err != nil {
			return fmt.Errorf("failed to start %s: %w", svc, err)
		}
	}
	
	// Wait for application
	time.Sleep(5 * time.Second)
	
	// Level 3: UI
	if err := c.StartService("ui"); err != nil {
		return fmt.Errorf("failed to start ui: %w", err)
	}
	
	// Level 4: Modules (basic)
	modulesBasic := []string{"module-executive", "module-planner", "module-memory", "module-reflective"}
	for _, svc := range modulesBasic {
		if err := c.StartService(svc); err != nil {
			return fmt.Errorf("failed to start %s: %w", svc, err)
		}
	}
	
	// Level 5: Modules (advanced)
	modulesAdvanced := []string{"module-learning", "module-metacognition", "module-autonomy"}
	for _, svc := range modulesAdvanced {
		if err := c.StartService(svc); err != nil {
			return fmt.Errorf("failed to start %s: %w", svc, err)
		}
	}
	
	return nil
}

// StopAllServices stops all ETHAN services in reverse order
func (c *Controller) StopAllServices() error {
	// Stop UI first
	if err := c.StopService("ui", 10); err != nil {
		return fmt.Errorf("failed to stop ui: %w", err)
	}
	
	// Stop modules (advanced)
	modulesAdvanced := []string{"module-learning", "module-metacognition", "module-autonomy"}
	for _, svc := range modulesAdvanced {
		if err := c.StopService(svc, 10); err != nil {
			return fmt.Errorf("failed to stop %s: %w", svc, err)
		}
	}
	
	// Stop modules (basic)
	modulesBasic := []string{"module-executive", "module-planner", "module-memory", "module-reflective"}
	for _, svc := range modulesBasic {
		if err := c.StopService(svc, 10); err != nil {
			return fmt.Errorf("failed to stop %s: %w", svc, err)
		}
	}
	
	// Stop application
	application := []string{"api", "kernel"}
	for _, svc := range application {
		if err := c.StopService(svc, 10); err != nil {
			return fmt.Errorf("failed to stop %s: %w", svc, err)
		}
	}
	
	// Stop runtime
	if err := c.StopService("runtime", 10); err != nil {
		return fmt.Errorf("failed to stop runtime: %w", err)
	}
	
	// Stop infrastructure
	infrastructure := []string{"nats", "redis", "postgres"}
	for _, svc := range infrastructure {
		if err := c.StopService(svc, 10); err != nil {
			return fmt.Errorf("failed to stop %s: %w", svc, err)
		}
	}
	
	return nil
}