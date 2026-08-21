import type { Meta, StoryObj } from "@storybook/react";
import { LifecycleStepper } from "./LifecycleStepper";

const meta: Meta<typeof LifecycleStepper> = {
  title: "Viz/LifecycleStepper",
  component: LifecycleStepper,
};

export default meta;
type Story = StoryObj<typeof LifecycleStepper>;

export const MidLifecycle: Story = {
  args: {
    label: "Meeting lifecycle",
    steps: [
      { id: "1", label: "Agenda draft", done: true, current: false },
      { id: "2", label: "Published", done: true, current: false },
      { id: "3", label: "In progress", done: false, current: true },
      { id: "4", label: "Minutes", done: false, current: false },
      { id: "5", label: "Approved", done: false, current: false },
    ],
  },
};
