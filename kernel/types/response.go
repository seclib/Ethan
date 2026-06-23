package types

import "time"

// ResponseStatus represents the outcome of a request.
type ResponseStatus string

const (
	ResponseStatusOK       ResponseStatus = "ok"
	ResponseStatusError    ResponseStatus = "error"
	ResponseStatusTimeout  ResponseStatus = "timeout"
	ResponseStatusRejected ResponseStatus = "rejected"
)

// Response is the structured output for a completed request.
type Response struct {
	ID         string
	RequestID  string
	Status     ResponseStatus
	Result     map[string]any
	Error      string
	Metadata   map[string]any
	Timestamp  int64
}

func generateID() string {
	return time.Now().Format("20060102150405.999999999")
}

// NewResponse creates a Response for a completed Request.
func NewResponse(req Request, status ResponseStatus, result map[string]any, err error) Response {
	resp := Response{
		ID:         generateID(),
		RequestID:  req.ID,
		Status:     status,
		Result:     result,
		Timestamp:  time.Now().Unix(),
	}
	if err != nil {
		resp.Error = err.Error()
	}
	return resp
}
