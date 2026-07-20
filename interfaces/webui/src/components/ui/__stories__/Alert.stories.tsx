import type { Meta, StoryObj } from "@storybook/react-vite";
import { Alert, AlertTitle, AlertDescription } from "../alert";

const meta: Meta<typeof Alert> = {
  title: "UI/Alert",
  component: Alert,
};

type Story = StoryObj<typeof Alert>;

export const Default: Story = {
  render: () => (
    <Alert>
      <AlertTitle>Title</AlertTitle>
      <AlertDescription>Description</AlertDescription>
    </Alert>
  ),
};

export default meta;