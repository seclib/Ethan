import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Textarea } from "@/components/ui/textarea";

const meta: Meta<typeof Textarea> = {
  title: "UI/Textarea",
  component: Textarea,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Textarea>;

export const Default: Story = {
  render: () => <Textarea placeholder="Enter your message..." />,
};

export const WithError: Story = {
  render: () => <Textarea error="This field is required" id="error-demo" />,
};

export const WithSuccess: Story = {
  render: () => <Textarea success value="Valid content" />,
};

export const NonResizable: Story = {
  render: () => <Textarea resizable={false} placeholder="Fixed size textarea" />,
};