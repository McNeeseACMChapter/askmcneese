import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import * as Tooltip from "@radix-ui/react-tooltip";
import { Bell, LogOut, Search, UserRound } from "lucide-react";
import { Link } from "react-router-dom";
import { usePrototype } from "../../state/PrototypeContext";
import { Button } from "../ui/Button";
import { IconButton } from "../ui/IconButton";
import { PrototypeBadge } from "./PrototypeBadge";

interface AcmRouteHeaderProps {
  breadcrumb?: string;
  primaryActionLabel?: string;
}

function Tip({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Tooltip.Root delayDuration={200}>
      <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
      <Tooltip.Portal>
        <Tooltip.Content
          className="rounded-md bg-brand-950 px-2 py-1 text-xs text-white"
          sideOffset={6}
        >
          {label}
          <Tooltip.Arrow className="fill-brand-950" />
        </Tooltip.Content>
      </Tooltip.Portal>
    </Tooltip.Root>
  );
}

export function AcmRouteHeader({
  breadcrumb,
  primaryActionLabel,
}: AcmRouteHeaderProps) {
  const { user } = usePrototype();

  return (
    <Tooltip.Provider>
      <header className="acm-route-header surface-nav">
        <div className="acm-route-header__left">
          {breadcrumb ? (
            <p className="acm-route-header__crumb">{breadcrumb}</p>
          ) : null}
        </div>
        <div className="acm-route-header__actions">
          {primaryActionLabel ? (
            <Button type="button" variant="primary">
              {primaryActionLabel}
            </Button>
          ) : null}
          <PrototypeBadge />
          <Tip label="Search is not connected yet">
            <IconButton label="Search unavailable" disabled>
              <Search size={18} strokeWidth={1.75} aria-hidden />
            </IconButton>
          </Tip>
          <Tip label="Notifications">
            <Link to="/notifications" className="acm-icon-btn" aria-label="Notifications">
              <Bell size={18} strokeWidth={1.75} aria-hidden />
            </Link>
          </Tip>
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button type="button" className="acm-icon-btn" aria-label="Profile menu">
                <UserRound size={18} strokeWidth={1.75} aria-hidden />
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="surface-interactive z-[500] min-w-[220px] p-2"
                sideOffset={8}
                align="end"
              >
                <div className="px-2 py-2">
                  <p className="text-sm font-semibold">{user.name}</p>
                  <p className="text-xs text-text-muted">
                    {user.roleLabel} · {user.termLabel}
                  </p>
                </div>
                <DropdownMenu.Separator className="my-1 h-px bg-[var(--border-subtle)]" />
                <DropdownMenu.Item asChild>
                  <Link
                    to="/profile"
                    className="block rounded-md px-2 py-2 text-sm text-text-primary outline-none hover:bg-surface-hover"
                  >
                    Profile
                  </Link>
                </DropdownMenu.Item>
                <DropdownMenu.Item asChild>
                  <Link
                    to="/fixtures"
                    className="block rounded-md px-2 py-2 text-sm text-text-primary outline-none hover:bg-surface-hover"
                  >
                    Fixture gallery
                  </Link>
                </DropdownMenu.Item>
                <DropdownMenu.Item asChild>
                  <Link
                    to="/login"
                    className="flex items-center gap-2 rounded-md px-2 py-2 text-sm text-text-primary outline-none hover:bg-surface-hover"
                  >
                    <LogOut size={16} strokeWidth={1.75} aria-hidden />
                    Sign out
                  </Link>
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </header>
    </Tooltip.Provider>
  );
}
