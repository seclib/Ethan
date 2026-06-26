package docker

import (
	"fmt"
	"strings"

	"github.com/seclib/Ethan/runtime/internal/socket"
)

// DockerHandler handles Docker-related commands
type DockerHandler struct {
	controller *Controller
}

// NewDockerHandler creates a new Docker handler
func NewDockerHandler(controller *Controller) *DockerHandler {
	return &DockerHandler{controller: controller}
}

// HandleCommand handles Docker commands (implements socket.CommandHandler)
func (h *DockerHandler) HandleCommand(cmd *socket.Command) *socket.Response {
	switch cmd.Type {
	case "services.start":
		return h.handleStartServices(cmd)
	case "services.stop":
		return h.handleStopServices(cmd)
	case "services.restart":
		return h.handleRestartServices(cmd)
	case "services.status":
		return h.handleGetStatus(cmd)
	case "services.logs":
		return h.handleGetLogs(cmd)
	default:
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": fmt.Sprintf("Unknown Docker command: %s", cmd.Type),
				"hint":    "Available: services.start, services.stop, services.restart, services.status, services.logs",
			},
		}
	}
}

// handleStartServices handles services.start command
func (h *DockerHandler) handleStartServices(cmd *socket.Command) *socket.Response {
	services, ok := cmd.Payload["services"].([]interface{})
	if !ok {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": "Missing 'services' array in payload",
			},
		}
	}

	// Start services
	var started []string
	for _, svc := range services {
		serviceName, ok := svc.(string)
		if !ok {
			continue
		}

		// Map service names
		containerName := h.mapServiceName(serviceName)

		if err := h.controller.StartService(containerName); err != nil {
			return &socket.Response{
				Type:      "error",
				SessionID: cmd.SessionID,
				Payload: map[string]interface{}{
					"code":    "SERVICE_START_FAILED",
					"message": fmt.Sprintf("Failed to start %s", serviceName),
					"details": err.Error(),
					"service": serviceName,
				},
			}
		}

		started = append(started, serviceName)
	}

	return &socket.Response{
		Type:      "services.started",
		SessionID: cmd.SessionID,
		Payload: map[string]interface{}{
			"success": true,
			"services": started,
		},
	}
}

// handleStopServices handles services.stop command
func (h *DockerHandler) handleStopServices(cmd *socket.Command) *socket.Response {
	services, ok := cmd.Payload["services"].([]interface{})
	if !ok {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": "Missing 'services' array in payload",
			},
		}
	}

	timeout := 30
	if t, ok := cmd.Payload["timeout"].(float64); ok {
		timeout = int(t)
	}

	// Stop services
	var stopped []string
	for _, svc := range services {
		serviceName, ok := svc.(string)
		if !ok {
			continue
		}

		// Map service names
		containerName := h.mapServiceName(serviceName)

		if err := h.controller.StopService(containerName, timeout); err != nil {
			return &socket.Response{
				Type:      "error",
				SessionID: cmd.SessionID,
				Payload: map[string]interface{}{
					"code":    "SERVICE_STOP_FAILED",
					"message": fmt.Sprintf("Failed to stop %s", serviceName),
					"details": err.Error(),
					"service": serviceName,
				},
			}
		}

		stopped = append(stopped, serviceName)
	}

	return &socket.Response{
		Type:      "services.stopped",
		SessionID: cmd.SessionID,
		Payload: map[string]interface{}{
			"success": true,
			"services": stopped,
		},
	}
}

// handleRestartServices handles services.restart command
func (h *DockerHandler) handleRestartServices(cmd *socket.Command) *socket.Response {
	services, ok := cmd.Payload["services"].([]interface{})
	if !ok {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": "Missing 'services' array in payload",
			},
		}
	}

	timeout := 30
	if t, ok := cmd.Payload["timeout"].(float64); ok {
		timeout = int(t)
	}

	// Restart services
	var restarted []string
	for _, svc := range services {
		serviceName, ok := svc.(string)
		if !ok {
			continue
		}

		// Map service names
		containerName := h.mapServiceName(serviceName)

		if err := h.controller.RestartService(containerName, timeout); err != nil {
			return &socket.Response{
				Type:      "error",
				SessionID: cmd.SessionID,
				Payload: map[string]interface{}{
					"code":    "SERVICE_RESTART_FAILED",
					"message": fmt.Sprintf("Failed to restart %s", serviceName),
					"details": err.Error(),
					"service": serviceName,
				},
			}
		}

		restarted = append(restarted, serviceName)
	}

	return &socket.Response{
		Type:      "services.restarted",
		SessionID: cmd.SessionID,
		Payload: map[string]interface{}{
			"success": true,
			"services": restarted,
		},
	}
}

// handleGetStatus handles services.status command
func (h *DockerHandler) handleGetStatus(cmd *socket.Command) *socket.Response {
	statuses, err := h.controller.GetStatus()
	if err != nil {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "STATUS_FAILED",
				"message": "Failed to get service status",
				"details": err.Error(),
			},
		}
	}

	// Format services
	services := make([]map[string]interface{}, len(statuses))
	for i, status := range statuses {
		services[i] = map[string]interface{}{
			"name":   status.Name,
			"state":  status.State,
			"health": status.Health,
			"id":     status.ID,
		}
	}

	return &socket.Response{
		Type:      "services.status.result",
		SessionID: cmd.SessionID,
		Payload: map[string]interface{}{
			"services": services,
		},
	}
}

// handleGetLogs handles services.logs command
func (h *DockerHandler) handleGetLogs(cmd *socket.Command) *socket.Response {
	serviceName, ok := cmd.Payload["service"].(string)
	if !ok {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "INVALID_REQUEST",
				"message": "Missing 'service' in payload",
			},
		}
	}

	tail := 100
	if t, ok := cmd.Payload["tail"].(float64); ok {
		tail = int(t)
	}

	// Map service name
	containerName := h.mapServiceName(serviceName)

	logs, err := h.controller.GetLogs(containerName, tail)
	if err != nil {
		return &socket.Response{
			Type:      "error",
			SessionID: cmd.SessionID,
			Payload: map[string]interface{}{
				"code":    "LOGS_FAILED",
				"message": fmt.Sprintf("Failed to get logs for %s", serviceName),
				"details": err.Error(),
			},
		}
	}

	return &socket.Response{
		Type:      "services.logs.result",
		SessionID: cmd.SessionID,
		Payload: map[string]interface{}{
			"service": serviceName,
			"logs":    logs,
		},
	}
}

// mapServiceName maps CLI service names to container names
func (h *DockerHandler) mapServiceName(serviceName string) string {
	// Remove "ethan-" prefix if present
	serviceName = strings.TrimPrefix(serviceName, "ethan-")

	// Add "ethan-" prefix for container name
	return "ethan-" + serviceName
}