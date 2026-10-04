import type { DispensingQuality } from "@/lib/api/types";

function Stars({ n }: { n: number }) {
  return (
    <span className="whitespace-nowrap text-amber-500" aria-label={`${n} of 5 stars`}>
      {"★".repeat(n)}
      <span className="text-muted-foreground/40">{"★".repeat(Math.max(0, 5 - n))}</span>
    </span>
  );
}

/**
 * The brief's Bonus 2, laid out the way the brief shows it: a star rating
 * per aspect and an overall score out of 100. It rates the deposits in the
 * photo, never the diagnosis — every rating is a count of deposits, said
 * next to it, so it can be checked on the annotated photo.
 */
export function DispensingQualityScore({ quality }: { quality: DispensingQuality }) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium text-muted-foreground">Dispensing quality</span>
        <span className="text-xs text-muted-foreground">
          <span className="text-lg font-semibold tabular-nums text-foreground">{quality.overall}</span>/100
        </span>
      </div>
      <dl className="space-y-1 text-xs">
        {quality.aspects.map((a) => (
          <div key={a.key} className="grid grid-cols-[minmax(0,9rem)_auto_1fr] items-baseline gap-x-2">
            <dt className="text-foreground">{a.label}</dt>
            <dd><Stars n={a.stars} /></dd>
            <dd className="truncate text-muted-foreground" title={a.detail}>{a.detail}</dd>
          </div>
        ))}
      </dl>
      <p className="text-[11px] text-muted-foreground">
        Overall: {quality.detail}. Rates the deposits in the photo, not how sure the diagnosis is.
      </p>
    </div>
  );
}
