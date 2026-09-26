// Horizontal bars of logged food categories — simple, legible, no legend needed.
export default function CategoryChart({ data }) {
  const max = Math.max(1, ...data.map((d) => d.count))
  return (
    <figure className="panel p-4">
      <figcaption className="mb-3 font-semibold">What you logged, by category</figcaption>
      <ul className="space-y-2">
        {data.slice(0, 8).map((d) => (
          <li key={d.category} className="grid grid-cols-[7.5rem_1fr_2rem] items-center gap-2 text-sm">
            <span className="truncate">{d.category}</span>
            <span className="h-3 rounded-sm bg-brand/80" style={{ width: `${(d.count / max) * 100}%` }} aria-hidden />
            <span className="text-right tabular text-muted">{d.count}</span>
          </li>
        ))}
      </ul>
    </figure>
  )
}
