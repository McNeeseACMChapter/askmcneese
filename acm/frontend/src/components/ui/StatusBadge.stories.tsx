import type { Meta, StoryObj } from "@storybook/react";
import { StatusBadge } from "./StatusBadge";

const meta: Meta<typeof StatusBadge> = {
  title: "UI/StatusBadge",
  component: StatusBadge,
};

export default meta;
type Story = StoryObj<typeof StatusBadge>;

export const Success: Story = { args: { label: "Approved", tone: "success" } };
export const Warning: Story = { args: { label: "Missing evidence", tone: "warning" } };
export const Danger: Story = { args: { label: "Declined", tone: "danger" } };
export const Muted: Story = { args: { label: "Archived", tone: "muted" } };
