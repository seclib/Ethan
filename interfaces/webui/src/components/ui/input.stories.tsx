import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./input";
import { Search, Eye } from "lucide-react";

const meta: Meta<typeof Input> = {
  title: "UI/Input",
  component: Input,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    type: {
      control: "select",
      options: ["text", "email", "password", "search"],
    },
    error: { control: "text" },
    success: { control: "boolean" },
    disabled: { control: "boolean" },
    placeholder: { control: "text" },
  },
};

export default meta;
type Story = StoryObj<typeof Input>;

export const Default: Story = {
  args: {
    placeholder: "Type something...",
  },
};

export const WithIcon: Story = {
  args: {
    icon: <Search />,
    placeholder: "Search...",
  },
};

export const WithIconRight: Story = {
  args: {
    iconRight: <Eye />,
    type: "password",
    placeholder: "Password",
  },
};

export const Error: Story = {
  args: {
    error: "This field is required",
    placeholder: "Email",
    id: "email-input",
  },
};

export const Success: Story = {
  args: {
    success: true,
    value: "valid@email.com",
    placeholder: "Email",
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    value: "Disabled input",
  },
};