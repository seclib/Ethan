package response

import (
	"ethan/kernel/types"
)

// Builder assembles Response objects from module outputs.
type Builder struct{}

// NewBuilder creates a Response Builder.
func NewBuilder() *Builder {
	return &Builder{}
}

// Build creates a Response from a Request and module output.
func (b *Builder) Build(req types.Request, result map[string]any, err error) types.Response {
	if err != nil {
		return types.NewResponse(req, types.ResponseStatusError, nil, err)
	}
	if result == nil {
		return types.NewResponse(req, types.ResponseStatusOK, map[string]any{}, nil)
	}
	return types.NewResponse(req, types.ResponseStatusOK, result, nil)
}