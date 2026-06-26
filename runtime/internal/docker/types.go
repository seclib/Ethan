package docker

// Command represents a Docker command
type Command struct {
	Type      string                 `json:"type"`
	SessionID string                 `json:"session_id"`
	Payload   map[string]interface{} `json:"payload"`
}

// Response represents a Docker command response
type Response struct {
	Type      string                 `json:"type"`
	SessionID string                 `json:"session_id"`
	Payload   map[string]interface{} `json:"payload"`
}