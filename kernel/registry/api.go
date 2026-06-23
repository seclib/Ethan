package registry

import (
	"encoding/json"
	"net/http"
)

// APIHandler serves registry data over HTTP.
type APIHandler struct {
	service *Service
}

// NewAPIHandler creates a new read-only registry API.
func NewAPIHandler(service *Service) *APIHandler {
	return &APIHandler{service: service}
}

// RegisterRoutes adds registry endpoints to mux.
func (h *APIHandler) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/registry/capabilities", h.ListCapabilities)
	mux.HandleFunc("/registry/capabilities/", h.GetCapability)
	mux.HandleFunc("/registry/modules", h.ListModules)
}

func (h *APIHandler) ListCapabilities(w http.ResponseWriter, r *http.Request) {
	caps := h.service.AllCapabilities()
	writeJSON(w, caps)
}

func (h *APIHandler) GetCapability(w http.ResponseWriter, r *http.Request) {
	name := r.URL.Path[len("/registry/capabilities/"):]
	caps, err := h.service.Resolve(name)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}
	writeJSON(w, caps[0])
}

func (h *APIHandler) ListModules(w http.ResponseWriter, r *http.Request) {
	modules := h.service.ActiveModules()
	writeJSON(w, modules)
}

func writeJSON(w http.ResponseWriter, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}