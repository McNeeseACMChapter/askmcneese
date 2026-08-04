import * as Popover from "@radix-ui/react-popover";
import { fixtureRepo } from "../../data/repository";
import { Button } from "../ui/Button";

export function PrototypeBadge() {
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button type="button" className="prototype-badge" aria-label="Prototype environment">
          Prototype
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="surface-interactive z-[600] max-w-xs p-4 outline-none"
          sideOffset={8}
          align="end"
        >
          <p className="text-sm font-semibold text-text-primary">Fixture environment</p>
          <p className="mt-2 text-xs text-text-secondary">
            Data is synthetic. Mutations update local fixture state only. No chapter
            records change. Reset restores the seed snapshot.
          </p>
          <div className="mt-3">
            <Button
              variant="secondary"
              onClick={() => {
                fixtureRepo.reset();
              }}
            >
              Reset fixtures
            </Button>
          </div>
          <Popover.Arrow className="fill-white" />
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
