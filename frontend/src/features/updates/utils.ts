const MONTHS = [
  "JAN",
  "FEB",
  "MAR",
  "APR",
  "MAY",
  "JUN",
  "JUL",
  "AUG",
  "SEP",
  "OCT",
  "NOV",
  "DEC",
] as const;

const LONG_MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
] as const;

function parts(iso: string): { year: string; month: string; day: string } {
  const [year, month, day] = iso.split("-");
  return { year, month, day };
}

/** Exact historical dates. Do not use relative language or local Date parsing. */
export function formatExactDate(iso: string): string {
  const { year, month, day } = parts(iso);
  const monthLabel = MONTHS[Number(month) - 1];
  return `${monthLabel} ${day}, ${year}`;
}

export function formatMonthDay(iso: string): string {
  const { month, day } = parts(iso);
  return `${MONTHS[Number(month) - 1]} ${day}`;
}

export function formatDateRange(startIso: string, endIso: string): string {
  const start = parts(startIso);
  const end = parts(endIso);
  const startMonth = MONTHS[Number(start.month) - 1];
  const endMonth = MONTHS[Number(end.month) - 1];
  if (start.year === end.year) {
    return `${startMonth} ${start.day} — ${endMonth} ${end.day}, ${end.year}`;
  }
  return `${startMonth} ${start.day}, ${start.year} — ${endMonth} ${end.day}, ${end.year}`;
}

export function formatSearchDates(iso: string): string {
  const { year, month, day } = parts(iso);
  const monthIndex = Number(month) - 1;
  const dayNum = String(Number(day));
  return [
    formatExactDate(iso),
    `${LONG_MONTHS[monthIndex]} ${dayNum}`,
    `${LONG_MONTHS[monthIndex]} ${dayNum}, ${year}`,
    `${MONTHS[monthIndex]} ${dayNum}`,
  ].join(" ");
}

export function chapterNumberLabel(number: number): string {
  return String(number).padStart(2, "0");
}

export function ticketAnchor(ticketNo: number): string {
  return `ticket-${ticketNo}`;
}

export function parseTicketHash(hash: string): number | null {
  const match = hash.match(/^ticket-(\d+)$/);
  if (!match) return null;
  return Number(match[1]);
}
