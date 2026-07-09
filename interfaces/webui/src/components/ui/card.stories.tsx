import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const meta: Meta<typeof Card> = {
  title: "UI/Card",
  component: Card,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Card>;

export const Default: Story = {
  render: () => (
    <Card variant="outlined" className="w-80">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground-secondary">
          This is the card content. You can put any content here.
        </p>
      </CardContent>
      <CardFooter>
        <Button variant="primary" className="w-full">Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const Variants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4">
      <Card variant="outlined" className="w-64">
        <CardHeader>
          <CardTitle>Outlined</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground-secondary">Outlined card variant</p>
        </CardContent>
      </Card>
      <Card variant="elevated" className="w-64">
        <CardHeader>
          <CardTitle>Elevated</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground-secondary">Elevated card with shadow</p>
        </CardContent>
      </Card>
    </div>
  ),
};

export const Hoverable: Story = {
  render: () => (
    <Card variant="outlined" hoverable className="w-80">
      <CardHeader>
        <CardTitle>Hoverable Card</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground-secondary">
          Hover over this card to see the effect.
        </p>
      </CardContent>
    </Card>
  ),
};