import { Camera, ClipboardCheck, MessageSquareText, type LucideIcon } from "lucide-react";

import type { Backing } from "@/lib/api/types";

function plural(n: number, word: string) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** "1 reason backs it", "3 reasons back it". */
function reasonsBack(n: number) {
  return `${plural(n, "reason")} back${n === 1 ? "s" : ""} it`;
}

/** The backing in one sentence, for the chat and the printed report. */
export function describeBacking(b: Backing): string {
  const parts = [
    b.measured ? `${b.measured} measured in the photo` : null,
    b.answers ? `${b.answers} from the answers` : null,
    b.checks ? plural(b.checks, "check") + " on this case" : null,
  ].filter(Boolean);
  const against = b.against ? `; ${b.against} against` : "";
  return b.reasons === 0
    ? "Nothing backs it yet: no rule fired for it."
    : `${reasonsBack(b.reasons)}: ${parts.join(", ")}${against}.`;
}

function Source({ icon: Icon, n, label }: { icon: LucideIcon; n: number; label: string }) {
  if (!n) return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-muted px-1.5 py-0.5" title={label}>
      <Icon className="size-3" aria-hidden />
      <span className="tabular-nums">{n}</span>
      <span className="sr-only">{label}</span>
    </span>
  );
}

/**
 * What backs the top cause, in place of a star rating. Stars read as
 * certainty and mixed two things nobody could trace; this is a count of
 * the reasons listed under "Why X%?", split by where each came from. The
 * evaluation measures it — the more reasons, the more often the top cause
 * is right.
 */
export function ReasonsBacking({ backing }: { backing: Backing }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
      <span className="font-medium text-foreground">
        {backing.reasons === 0 ? "Nothing backs it yet" : reasonsBack(backing.reasons)}
      </span>
      <Source icon={Camera} n={backing.measured} label="measured in the photo" />
      <Source icon={MessageSquareText} n={backing.answers} label="from the answers" />
      <Source icon={ClipboardCheck} n={backing.checks} label="checks on this case" />
      {backing.against > 0 && <span>&middot; {backing.against} against</span>}
    </div>
  );
}
