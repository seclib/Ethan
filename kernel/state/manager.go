package state

import (
	"ethan/kernel/types"
)

// Manager abstracts state storage.
type Manager struct {
	readStore  ReadStore
	writeStore WriteStore
}

// ReadStore defines read operations.
type ReadStore interface {
	Get(key string) ([]byte, error)
}

// WriteStore defines write operations.
type WriteStore interface {
	Set(key string, value []byte) error
}

// NewManager creates a State Manager.
func NewManager(r ReadStore, w WriteStore) *Manager {
	return &Manager{readStore: r, writeStore: w}
}

// Get retrieves a value.
func (m *Manager) Get(key string) ([]byte, error) {
	return m.readStore.Get(key)
}

// Set stores a value.
func (m *Manager) Set(key string, value []byte) error {
	return m.writeStore.Set(key, value)
}

// SaveResponse persists a Response.
func (m *Manager) SaveResponse(resp types.Response) error {
	data, _ := json.Marshal(resp)
	return m.writeStore.Set("response:"+resp.ID, data)
}

// LoadResponses retrieves recent responses (implemented by concrete store).
func (m *Manager) LoadResponses(limit int) ([][]byte, error) {
	return nil, nil // placeholder
}