export function AvatarGroup({
  people,
}: {
  people: { name: string; initials: string }[];
}) {
  return (
    <ul className="acm-avatars" aria-label="Team">
      {people.map((p) => (
        <li key={p.name} title={p.name} className="acm-avatars__item">
          <span aria-hidden>{p.initials}</span>
          <span className="sr-only">{p.name}</span>
        </li>
      ))}
    </ul>
  );
}
