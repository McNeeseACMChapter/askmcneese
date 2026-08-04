import type { ReactNode } from "react";
import { SearchField } from "./SearchField";

interface FilterBarProps {
  search: string;
  onSearch: (v: string) => void;
  children?: ReactNode;
}

export function FilterBar({ search, onSearch, children }: FilterBarProps) {
  return (
    <div className="filter-bar">
      <div className="filter-bar__search">
        <SearchField value={search} onChange={onSearch} placeholder="Search projects" />
      </div>
      <div className="filter-bar__controls">{children}</div>
    </div>
  );
}
