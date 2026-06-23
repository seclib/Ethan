package main

import (
	"fmt"
	"os"

	"ethan/kernel/bus"
	"ethan/kernel/registry"
	"ethan/kernel/service"
)

func main() {
	// 1. Connect to NATS
	nc, err := bus.Connect("nats://localhost:4222")
	if err != nil {
		fmt.Println("connect error:", err)
		os.Exit(1)
	}
	defer nc.Close()

	// 2. Initialize registry
	reg := registry.NewService()

	// 3. Initialize kernel service
	kernel := service.NewService(nc, reg)

	// 4. Subscribe to interface events
	_, err = nc.Subscribe("ethan.interface.>", func(msg []byte) {
		ev := bus.ParseEvent(msg)
		kernel.HandleEvent(ev)
	})
	if err != nil {
		fmt.Println("subscribe error:", err)
		os.Exit(1)
	}

	fmt.Println("ETHAN Kernel v1 running")
	// 5. Block forever
	select {}
}
