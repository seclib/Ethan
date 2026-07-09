import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";

const meta: Meta<typeof Skeleton> = {
  title: "UI/Skeleton",
  component: Skeleton,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Skeleton>;

export const Text: Story = {
  render: () => (
    <div className="w-80 space-y-2">
      <Skeleton variant="text" lines={3} />
    </div>
  ),
};

export const Circle: Story = {
  render: () => (
    <div className="flex gap-4">
      <Skeleton variant="circle" className="w-12 h-12" />
      <Skeleton variant="circle" className="w-16 h-16" />
      <Skeleton variant="circle" className="w-20 h-20" />
    </div>
  ),
};

export const Rectangle: Story = {
  render: () => (
    <div className="w-80 space-y-2">
      <Skeleton variant="rectangle" className="w-full h-32" />
      <Skeleton variant="rectangle" className="w-full h-32" />
    </div>
  ),
};