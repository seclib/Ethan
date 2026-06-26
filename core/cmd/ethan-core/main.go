// ETHAN Core — AI Brain
// Entry point: parses config, injects dependencies, starts kernel.
//
// ZÉRO connaissance de Docker, systemd, terminal ou CLI.
// Communication: NATS (internal), gRPC (Runtime), HTTP (API).

package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"google.golang.org/grpc"
	"gopkg.in/yaml.v3"

	"github.com/nats-io/nats.go"
	"github.com/redis/go-redis/v9"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/ethan/core/internal/kernel"
	"github.com/ethan/core/internal/registry"
	"github.com/ethan/core/internal/bus"
	"github.com/ethan/core/internal/api"
	"github.com/ethan/core/internal/telemetry"
	"github.com/ethan/core/pkg/types"
)

type Config struct {
	NATS    string `yaml:"nats_url"`
	Redis   string `yaml:"redis_url"`
	Postgres string `yaml:"postgres_url"`
	GRPCPort int    `yaml:"grpc_port"`
	HTTPPort int    `yaml:"http_port"`
	LogLevel string `yaml:"log_level"`
}

func loadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}

	cfg := &Config{
		NATS:     "nats://localhost:4222",
		Redis:    "redis://localhost:6379/0",
		Postgres: "postgres://ethan:password@localhost:5432/ethan",
		GRPCPort: 50051,
		HTTPPort: 8000,
		LogLevel: "info",
	}

	if err := yaml.Unmarshal(data, cfg); err != nil {
		return nil, fmt.Errorf("parse config: %w", err)
	}

	return cfg, nil
}

func main() {
	configPath := "/etc/ethan/core.yaml"
	if p := os.Getenv("ETHAN_CORE_CONFIG"); p != "" {
		configPath = p
	}

	cfg, err := loadConfig(configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// ── NATS ──────────────────────────────────────────────────────
	nc, err := nats.Connect(cfg.NATS)
	if err != nil {
		log.Fatalf("Failed to connect to NATS: %v", err)
	}
	defer nc.Close()

	eventBus := bus.NewNATSBus(nc)

	// ── Redis ─────────────────────────────────────────────────────
	rdb := redis.NewClient(&redis.Options{
		Addr: cfg.Redis,
	})
	if err := rdb.Ping(ctx).Err(); err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	defer rdb.Close()

	// ── PostgreSQL ────────────────────────────────────────────────
	pool, err := pgxpool.New(ctx, cfg.Postgres)
	if err != nil {
		log.Fatalf("Failed to connect to PostgreSQL: %v", err)
	}
	defer pool.Close()

	// ── Registry ──────────────────────────────────────────────────
	modRegistry := registry.NewModuleRegistry(eventBus)

	// ── Kernel ────────────────────────────────────────────────────
	k := kernel.NewCognitiveKernel(eventBus, rdb, pool, modRegistry, cfg.LogLevel)

	// ── gRPC Server ───────────────────────────────────────────────
	grpcListener, err := net.Listen("tcp", fmt.Sprintf(":%d", cfg.GRPCPort))
	if err != nil {
		log.Fatalf("Failed to listen gRPC: %v", err)
	}

	grpcServer := grpc.NewServer()
	api.RegisterCoreServer(grpcServer, k)

	go func() {
		log.Printf("gRPC server listening on :%d", cfg.GRPCPort)
		if err := grpcServer.Serve(grpcListener); err != nil {
			log.Printf("gRPC server error: %v", err)
		}
	}()

	// ── HTTP Server ───────────────────────────────────────────────
	httpServer := api.NewHTTPServer(k, cfg.HTTPPort)
	go func() {
		log.Printf("HTTP server listening on :%d", cfg.HTTPPort)
		if err := httpServer.ListenAndServe(); err != nil {
			log.Printf("HTTP server error: %v", err)
		}
	}()

	// ── Telemetry ─────────────────────────────────────────────────
	telemetry.Start(ctx)

	// ── Start Kernel ──────────────────────────────────────────────
	if err := k.Start(); err != nil {
		log.Fatalf("Failed to start kernel: %v", err)
	}

	log.Printf("ETHAN Core started (pid: %d)", os.Getpid())

	// ── Wait for signal ───────────────────────────────────────────
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	sig := <-sigCh

	log.Printf("Received signal: %v, shutting down...", sig)

	// ── Shutdown ──────────────────────────────────────────────────
	k.Stop()
	grpcServer.GracefulStop()
	httpServer.Shutdown(ctx)
	cancel()

	log.Println("ETHAN Core stopped")
}