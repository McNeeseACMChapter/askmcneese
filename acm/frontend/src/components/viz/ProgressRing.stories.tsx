import type { Meta, StoryObj } from "@storybook/react";
import { ProgressRing } from "./ProgressRing";

const meta: Meta<typeof ProgressRing> = {
  title: "Viz/ProgressRing",
  component: ProgressRing,
};

export default meta;
type Story = StoryObj<typeof ProgressRing>;

export const Default: Story = { args: { value: 72, label: "Evidence completeness" } };
export const Empty: Story = { args: { value: 0, label: "No progress" } };
export const Complete: Story = { args: { value: 100, label: "Complete" } };
