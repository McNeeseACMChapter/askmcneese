import { Search } from "lucide-react";

interface SearchFieldProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
}

export function SearchField({
  value,
  onChange,
  placeholder = "Search",
  label = "Search",
}: SearchFieldProps) {
  return (
    <div className="acm-search">
      <Search className="acm-search__icon" size={18} strokeWidth={1.75} aria-hidden />
      <label className="sr-only" htmlFor="acm-search-input">
        {label}
      </label>
      <input
        id="acm-search-input"
        className="acm-input"
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
