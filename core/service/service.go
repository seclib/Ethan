package service

import (
	"ethan/kernel/bus"
	"ethan/kernel/executor"
	"ethan/kernel/ingest"
	"ethan/kernel/intent"
	"ethan/kernel/planner"
	"ethan/kernel/registry"
	"ethan/kernel/resolver"
	"ethan/kernel/response"
	"ethan/kernel/types"
)

// Service assembles all kernel subsystems.
type Service struct {
	bus       *bus.EventBus
	ingest    *ingest.Ingest
	intent    *intent.Engine
	reg       *registry.Service
	resolver  *resolver.Resolver
	planner   *planner.Planner
	executor  *executor.Executor
	builder   *response.Builder
}

// NewService wires all subsystems together.
func NewService(b *bus.EventBus, reg *registry.Service) *Service {
	return &Service{
		bus:       b,
		ingest:    ingest.NewIngest(b),
		intent:    intent.NewEngine(),
		reg:       reg,
		resolver:  resolver.NewResolver(reg),
		planner:   planner.NewPlanner(reg),
		executor:  executor.NewExecutor(b),
		builder:   response.NewBuilder(),
	}
}

// HandleEvent is the main entry point for processing a kernel event.
func (s *Service) HandleEvent(ev types.Event) {
	s.ingest.Process(ev)
	intent := s.intent.Extract(ev)
	req := types.NewRequest(ev, intent.Name, []string{intent.Name}, types.RequestContext{
		SessionID:       ev.Context["session_id"],
		CorrelationID:   ev.ID,
		SourceInterface: ev.Source,
		Timestamp:       ev.Timestamp.Unix(),
	})
	plan, err := s.planner.Decompose(req)
	if err != nil || plan == nil {
		return
	}
	results := s.executor.Execute(*plan)
	_ = results
}
