import type { KeyboardEvent } from "react";
import type { ProjectUpdate } from "./types";
import { formatExactDate, ticketAnchor } from "./utils";

interface EventLedgerProps {
  events: ProjectUpdate[];
  openTicketNos: Set<number>;
  onToggleTicket: (ticketNo: number) => void;
}

function engineeringReference(event: ProjectUpdate): string | null {
  const parts = [event.pullRequest, event.commit, event.sprint].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function EventLedger({ events, openTicketNos, onToggleTicket }: EventLedgerProps) {
  if (events.length === 0) {
    return <p className="updatesEmpty">No recorded development events match this search.</p>;
  }

  return (
    <div className="updatesLedger">
      <h3 className="updatesLedger__title">Development log — {events.length} event{events.length === 1 ? "" : "s"}</h3>
      <ul className="updatesLedger__list">
        {events.map((event) => {
          const open = openTicketNos.has(event.ticketNo);
          const panelId = `${ticketAnchor(event.ticketNo)}-panel`;
          const reference = engineeringReference(event);
          return (
            <li key={event.ticketNo} id={ticketAnchor(event.ticketNo)} className="updatesEvent">
              <button
                type="button"
                className="updatesEvent__toggle"
                aria-expanded={open}
                aria-controls={panelId}
                onClick={() => onToggleTicket(event.ticketNo)}
                onKeyDown={(nativeEvent: KeyboardEvent<HTMLButtonElement>) => {
                  if (nativeEvent.key === "Enter" || nativeEvent.key === " ") {
                    nativeEvent.preventDefault();
                    onToggleTicket(event.ticketNo);
                  }
                }}
              >
                <time dateTime={event.date}>{formatExactDate(event.date)}</time>
                <span className="updatesEvent__title">
                  {event.turningPoint && <span className="updatesTurningPoint">Turning point</span>}
                  {event.title}
                </span>
                <span className="updatesEvent__areas">{event.areas.join(" · ")}</span>
                <span className="updatesEvent__chevron" aria-hidden="true" />
              </button>
              <div id={panelId} hidden={!open} className="updatesEvent__detail">
                {open ? (
                  <>
                    <p>
                      <span className="updatesKicker">What changed</span>
                      {event.title}
                    </p>
                    {event.notes && (
                      <p>
                        <span className="updatesKicker">Technical work</span>
                        <span className="updatesEvent__notes">{event.notes}</span>
                      </p>
                    )}
                    <p>
                      <span className="updatesKicker">Technology stack</span>
                      {event.technologies.length > 0 ? (
                        <span className="updatesTechnologyList">
                          {event.technologies.map((technology) => (
                            <span key={technology}>{technology}</span>
                          ))}
                        </span>
                      ) : (
                        <span>Non-implementation project event; no software stack applied.</span>
                      )}
                    </p>
                    {event.method && (
                      <p>
                        <span className="updatesKicker">Delivery method / tooling</span>
                        {event.method}
                      </p>
                    )}
                    <p>
                      <span className="updatesKicker">Contributors</span>
                      {event.contributors
                        .map((contributor) =>
                          contributor.role ? `${contributor.name} — ${contributor.role}` : contributor.name,
                        )
                        .join("; ")}
                    </p>
                    {reference && (
                      <p>
                        <span className="updatesKicker">Engineering reference</span>
                        <code className="updatesCode">{reference}</code>
                      </p>
                    )}
                    <p className="updatesEvent__ticket">Ticket {event.ticketNo}</p>
                  </>
                ) : null}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
