import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";

function ToastDemo() {
  const { addToast } = useToast();

  return (
    <div className="flex flex-wrap gap-2">
      <Button onClick={() => addToast({ title: "Success", message: "Operation completed", type: "success" })}>
        Success
      </Button>
      <Button onClick={() => addToast({ title: "Error", message: "Something went wrong", type: "error" })}>
        Error
      </Button>
      <Button onClick={() => addToast({ title: "Warning", message: "Check your input", type: "warning" })}>
        Warning
      </Button>
      <Button onClick={() => addToast({ title: "Info", message: "New update available", type: "info" })}>
        Info
      </Button>
    </div>
  );
}

const meta: Meta<typeof ToastProvider> = {
  title: "UI/Toast",
  component: ToastProvider,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof ToastProvider>;

export const Default: Story = {
  render: () => (
    <ToastProvider>
      <ToastDemo />
    </ToastProvider>
  ),
};