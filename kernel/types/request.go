package types

// Request represents an internal kernel request derived from an inbound event.
type Request struct {
	ID                  string
	Event               Event
	Intent               string
	Context              RequestContext
	RequiredCapabilities []string
	Constraints          map[string]any
}

// RequestContext holds metadata for request tracing.
type RequestContext struct {
	SessionID       string
	UserID          string
	CorrelationID   string
	SourceInterface string
	Timestamp       int64
}

// NewRequest creates a Request from an Event.
func NewRequest(event Event, intent string, caps []string, ctx RequestContext) Request {
	return Request{
		ID:                  event.ID,
		Event:               event,
		Intent:               intent,
		Context:              ctx,
		RequiredCapabilities: caps,
		Constraints:          make(map[string]any),
	}
}