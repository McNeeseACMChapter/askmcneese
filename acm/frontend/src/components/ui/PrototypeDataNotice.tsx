/** @deprecated Use PrototypeBadge in the shell. Kept for Storybook/fixture stories. */
export function PrototypeDataNotice({ extra }: { extra?: string }) {
  return (
    <p className="sr-only">
      Prototype fixture environment. {extra ?? "No real chapter records change."}
    </p>
  );
}
