import { ShieldOff } from "lucide-react";
import { Surface } from "./Surface";

export function PermissionNotice({
  title = "Permission denied",
  body = "Your fixture role cannot access this destination. Navigation remains stable; the destination is disabled or redirected.",
}: {
  title?: string;
  body?: string;
}) {
  return (
    <Surface level="content" className="p-8">
      <div className="flex flex-col items-start gap-3">
        <ShieldOff size={28} strokeWidth={1.75} className="text-text-muted" aria-hidden />
        <h1>{title}</h1>
        <p className="page-lede">{body}</p>
      </div>
    </Surface>
  );
}
