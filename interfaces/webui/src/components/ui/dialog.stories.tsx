import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const meta: Meta<typeof Dialog> = {
  title: "UI/Dialog",
  component: Dialog,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
};

export default meta;
type Story = StoryObj<typeof Dialog>;

export const Default: Story = {
  render: () => {
    const [open, setOpen] = React.useState(false);
    return (
      <>
        <Button onClick={() => setOpen(true)}>Open Dialog</Button>
        <Dialog
          open={open}
          onOpenChange={setOpen}
          title="Dialog Title"
        >
          <p className="text-sm text-foreground-secondary">
            This is a description of the dialog. It provides context for the user.
          </p>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
            <Button onClick={() => setOpen(false)}>Confirm</Button>
          </div>
        </Dialog>
      </>
    );
  },
};

export const Sizes: Story = {
  render: () => {
    const [size, setSize] = React.useState<"sm" | "md" | "lg" | "xl">("md");
    const [open, setOpen] = React.useState(false);
    return (
      <div className="flex gap-2">
        <Button onClick={() => setSize("sm")} variant="outline">Small</Button>
        <Button onClick={() => setSize("md")} variant="outline">Medium</Button>
        <Button onClick={() => setSize("lg")} variant="outline">Large</Button>
        <Button onClick={() => setSize("xl")} variant="outline">XL</Button>
        <Dialog open={open} onOpenChange={setOpen} title={`${size.toUpperCase()} Dialog`} size={size}>
          <p className="text-sm text-foreground-secondary">This is a {size} sized dialog.</p>
          <div className="flex justify-end gap-2 mt-4">
            <Button onClick={() => setOpen(false)}>Close</Button>
          </div>
        </Dialog>
      </div>
    );
  },
};
