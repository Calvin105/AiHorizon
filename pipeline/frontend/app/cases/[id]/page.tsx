"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft, ArrowRight, ChevronRight, Compass, FileText, LifeBuoy, NotebookPen, Sparkles, type LucideIcon,
} from "lucide-react";

import { ArtifactPanel, type Artifacts } from "@/components/wizard/artifact-panel";
import { EngineerNotes, markReviewed } from "@/components/engineer-notes";
import { ReasonsBacking } from "@/components/reasons-backing";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { TierInfo } from "@/components/tier-info";
import { ApiError } from "@/lib/api/client";
import { getCase } from "@/lib/api/cases";
import { getFollowupBank, getIntakeSpec } from "@/lib/api/intake";
import { getReport, previewClose } from "@/lib/api/report";
import type { Case, CheckOutcome, CloseCaseResponse, VisionResult } from "@/lib/api/types";
import { CLOSE_MEANING, DIAGNOSED_WORDS } from "@/lib/close";

function yesNo(value?: boolean | null) {
  return value ? "yes" : "no";
}

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

const OUTCOME_VARIANT: Record<CheckOutcome, "default" | "secondary" | "destructive"> = {
  confirms: "default",
  rules_out: "destructive",
  inconclusive: "secondary",
};

/** The close tier's colour: only CONFIRMED claims a fix. */
const VERDICT_TONE: Record<string, string> = {
  CONFIRMED: "text-emerald-700 dark:text-emerald-400",
  PLAUSIBLE: "text-amber-700 dark:text-amber-400",
  UNVERIFIED: "text-rose-700 dark:text-rose-400",
};

/**
 * The case's hub, laid out like the home page: where the case stands and
 * what to do next first, in the middle of the screen, and the records it
 * rests on folded away underneath. Every flow on a case comes back here.
 */
export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = Number(params.id);

  const [artifacts, setArtifacts] = React.useState<Artifacts | null>(null);
  const [caseData, setCaseData] = React.useState<Case | null>(null);
  const [closePreview, setClosePreview] = React.useState<CloseCaseResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    getCase(caseId)
      .then(async (c) => {
        if (cancelled) return;
        setCaseData(c);
        // The report is compiled on demand, not stored on the case — fetch
        // it too so a past case reads the same as a freshly-finished one.
        // No LLM explanation here: browsing a case shouldn't spend a call.
        const [report, preview, questions, followupQuestions] = await Promise.all([
          c.ranking ? getReport(caseId, false).catch(() => null) : Promise.resolve(null),
          // What's still unproved, from the same five conditions close uses.
          previewClose(caseId).catch(() => null),
          // The question spine, so the answers read in the words they were
          // asked in rather than as stored ids.
          getIntakeSpec().catch(() => []),
          getFollowupBank().catch(() => []),
        ]);
        if (cancelled) return;
        setClosePreview(preview);
        setArtifacts({
          caseData: c,
          photoUrl: null,
          questions,
          axes: c.fingerprint?.axes ?? {},
          axisNotes: c.fingerprint?.axis_notes ?? {},
          followups: c.fingerprint?.followups ?? {},
          followupQuestions,
          vision: (c.vision_result as VisionResult | null) ?? null,
          coarse: null,
          // The report already carries the same tally, so it's reused
          // rather than re-fetched.
          precedents: report?.precedents ?? null,
          ranking: c.ranking,
          comparison: null,
          checks: c.check_results ?? [],
          report,
          close: c.tier ? { tier: c.tier, gaps: c.closed_at ? (preview?.gaps ?? []) : [] } : null,
        });
      })
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : "Could not reach the API."));
    return () => {
      cancelled = true;
    };
  }, [caseId]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (!caseData || !artifacts) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-10 sm:px-6">
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  const closed = Boolean(caseData.closed_at);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-5 px-4 py-8 sm:px-6 sm:py-10">
      <div className="flex items-center justify-between gap-3">
        <Link
          href="/cases"
          className={buttonVariants({ variant: "ghost", size: "sm", className: "-ml-2 gap-1.5" })}
        >
          <ArrowLeft className="size-4" />
          All cases
        </Link>
        <TierInfo />
      </div>

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">
          Case #{caseData.case_id} &middot; {caseData.complaint ?? "unclassified"}
        </h1>
        <p className="text-sm text-muted-foreground">
          {caseData.station.name} &middot; {caseData.profile.name} &middot; {caseData.profile.material.name}
        </p>
      </div>

      <Verdict caseData={caseData} preview={closePreview} />

      {caseData.escalate && (
        <ReviewPanel caseData={caseData} onChange={(updated) => setCaseData(updated)} />
      )}

      {/* The actions. The one this case is waiting for is full width, as on
          the home page; the rest share the row under it. */}
      <nav className="grid grid-cols-2 gap-3" aria-label="Case actions">
        <Link
          href={`/troubleshoot/${caseData.case_id}`}
          className="group col-span-2 flex items-center gap-4 rounded-xl bg-primary p-4 text-primary-foreground shadow-sm transition-opacity hover:opacity-90 sm:p-5"
        >
          <span className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-primary-foreground/15">
            <Sparkles className="size-5" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block text-base font-semibold">
              {closed ? "Reopen and log a check" : "Continue troubleshooting"}
            </span>
            <span className="block text-sm opacity-80">
              {closed
                ? "The causes re-rank, and closing again re-scores what's been proved"
                : "Picks up where the case left off"}
            </span>
          </span>
          <ArrowRight className="size-5 shrink-0 transition-transform group-hover:translate-x-0.5" />
        </Link>
        <Tile
          href={`/cases/${caseData.case_id}/report`}
          icon={FileText}
          label="Report"
          hint="Every step on one printable page"
        />
        <Tile
          href={caseData.escalate ? "#review" : "#notes"}
          icon={caseData.escalate ? LifeBuoy : NotebookPen}
          label={caseData.escalate ? "Answer the operator" : "Engineer notes"}
          hint={caseData.engineer_notes ? "Written — read or edit" : "None yet"}
        />
      </nav>

      {/* Under review, the notes box is in the review panel, next to the
          question it answers. */}
      {!caseData.escalate && (
        <section id="notes" className="scroll-mt-6 space-y-1">
          {caseData.escalation_note && (
            <p className="text-sm text-muted-foreground">
              The operator asked: &ldquo;{caseData.escalation_note}&rdquo; &middot; reviewed
            </p>
          )}
          <EngineerNotes
            caseId={caseId}
            initial={caseData.engineer_notes}
            onSaved={(notes) => setCaseData((prev) => (prev ? { ...prev, engineer_notes: notes } : prev))}
          />
        </section>
      )}

      <Details caseData={caseData} artifacts={artifacts} />
    </div>
  );
}

/** Where the case stands, in the order someone deciding what to do reads
 * it: the verdict, the cause and what it rests on, and what isn't proved. */
function Verdict({ caseData, preview }: { caseData: Case; preview: CloseCaseResponse | null }) {
  const closed = Boolean(caseData.closed_at);
  const ranking = caseData.ranking;
  const top = ranking?.pass1[0];
  const confirmedTop = caseData.diagnosed === "check_confirmed" && caseData.diagnosis?.cause_id === top?.cause_id;
  const meaning = closed && caseData.tier ? CLOSE_MEANING[caseData.tier] : null;

  const headline = closed ? (caseData.tier ?? "Closed") : caseData.escalate ? "Waiting for an engineer" : "In progress";
  const subline = closed
    ? meaning?.headline
    : !ranking
      ? "Not ranked yet — the photo and the interview come first"
      : caseData.verification
        ? "Re-measured after the fix — ready to close"
        : "Ranked — testing the causes";

  return (
    <section className="space-y-4 rounded-xl bg-muted/60 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p
            className={`text-3xl font-bold tracking-tight ${
              closed && caseData.tier ? VERDICT_TONE[caseData.tier] : caseData.escalate ? "text-destructive" : ""
            }`}
          >
            {headline}
          </p>
          <p className="text-sm font-medium">{subline}</p>
        </div>
        <p className="shrink-0 text-right text-xs text-muted-foreground">
          {closed && caseData.closed_at ? `Closed ${shortDate(caseData.closed_at)}` : `Opened ${shortDate(caseData.opened_at)}`}
        </p>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <span className="rounded-md bg-background px-2 py-1">{DIAGNOSED_WORDS[caseData.diagnosed] ?? caseData.diagnosed}</span>
        <span className="rounded-md bg-background px-2 py-1">
          {caseData.action_count} changed &middot; {caseData.observation_count} looked
        </span>
      </div>

      {ranking && top && (
        <div className="space-y-1.5 border-t border-border/60 pt-3">
          <p className="text-xs text-muted-foreground">
            {confirmedTop ? "Cause, confirmed by a check" : "Leading cause"}
          </p>
          <p className="flex items-baseline justify-between gap-3">
            <span className="font-semibold leading-snug">{top.label}</span>
            <span className="shrink-0 font-mono font-semibold">{Math.round(top.likelihood * 100)}%</span>
          </p>
          <p className="text-xs text-muted-foreground">
            <span className="mr-1.5 rounded bg-background px-1.5 py-0.5 font-semibold text-foreground">{ranking.tier}</span>
            {ranking.tier_reason}
          </p>
          {ranking.backing && <ReasonsBacking backing={ranking.backing} />}
        </div>
      )}

      {preview && (preview.gaps.length > 0 ? (
        <div className="border-t border-border/60 pt-3">
          <p className="text-xs font-medium">
            {closed ? "What wasn't proved" : "Still needed to close CONFIRMED"}
          </p>
          <ul className="mt-1 ml-4 list-disc space-y-0.5 text-xs text-muted-foreground">
            {preview.gaps.map((gap) => <li key={gap}>{gap}</li>)}
          </ul>
        </div>
      ) : !closed ? (
        <p className="border-t border-border/60 pt-3 text-xs font-medium">
          All five conditions are met: closing now records CONFIRMED.
        </p>
      ) : null)}
    </section>
  );
}

function Tile({ href, icon: Icon, label, hint }: { href: string; icon: LucideIcon; label: string; hint: string }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 rounded-xl bg-muted/60 p-3 transition-colors hover:bg-muted sm:p-4"
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-background">
        <Icon className="size-5" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm leading-tight font-medium sm:text-base">{label}</span>
        <span className="block truncate text-xs text-muted-foreground">{hint}</span>
      </span>
    </Link>
  );
}

/** Shown while the case is escalated: the operator's question, and the
 * reviewer's two moves — answer in the notes, or take over in the wizard
 * and log a check (the action button below). There is no way to set the
 * cause from here on purpose: only a check can prove one (DESIGN.md step 8). */
function ReviewPanel({ caseData, onChange }: { caseData: Case; onChange: (updated: Case) => void }) {
  return (
    <section id="review" className="scroll-mt-6 space-y-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4">
      <div className="min-w-0 space-y-1">
        <p className="flex items-center gap-1.5 text-sm font-medium text-destructive">
          <LifeBuoy className="size-4" />
          An operator asked for help
        </p>
        <p className="text-base font-semibold text-foreground">
          {caseData.escalation_note ? `“${caseData.escalation_note}”` : "No question given."}
        </p>
      </div>
      <EngineerNotes
        caseId={caseData.case_id}
        initial={caseData.engineer_notes}
        onSaved={(notes) => onChange({ ...caseData, engineer_notes: notes })}
        onMarkReviewed={async (notes) => {
          const updated = await markReviewed(caseData.case_id, notes);
          if (updated) onChange(updated);
        }}
        placeholder="Answer the operator — what to check next, what you ruled out. They see this the next time they open the case."
      />
    </section>
  );
}

/** The records the verdict rests on, folded away: someone deciding what to
 * do next rarely needs the valve model, but someone checking the work does. */
function Details({ caseData, artifacts }: { caseData: Case; artifacts: Artifacts }) {
  return (
    <details className="group rounded-xl border">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium select-none [&::-webkit-details-marker]:hidden">
        <ChevronRight className="size-4 transition-transform group-open:rotate-90" />
        Details
        <span className="font-normal text-muted-foreground">
          — station, material, profile, checks and diagnostic artifacts
        </span>
      </summary>
      <Tabs defaultValue="context" className="border-t p-4">
        <TabsList className="mb-4">
          <TabsTrigger value="context">Links & Context</TabsTrigger>
          <TabsTrigger value="artifacts">Diagnostic Artifacts</TabsTrigger>
        </TabsList>

        <TabsContent value="context" className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-3">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-sm">Station</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Field label="Name" value={caseData.station.name} />
              <Field label="Line" value={caseData.station.line} />
              <Field label="Dispenser class" value={caseData.station.dispenser_class.replaceAll("_", "-")} />
              <Field label="Valve model" value={caseData.station.valve_model ?? "—"} />
              <Field label="Heated reservoir" value={yesNo(caseData.station.heated_reservoir)} />
              <Field label="Camera available" value={yesNo(caseData.station.camera_available)} />
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-sm">Material</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Field label="Name" value={caseData.profile.material.name} />
              <Field label="Family" value={caseData.profile.material.family.replaceAll("_", " ")} />
              <Field label="Part number" value={caseData.profile.material.part_number ?? "—"} />
              <Field label="Lot" value={caseData.material_lot ?? "—"} />
              <Field
                label="Two-part / thixotropic"
                value={`${yesNo(caseData.profile.material.two_part)} / ${yesNo(caseData.profile.material.thixotropic)}`}
              />
              <Field
                label="Pot life"
                value={caseData.profile.material.pot_life_hours != null ? `${caseData.profile.material.pot_life_hours} h` : "—"}
              />
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-sm">Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Field label="Name" value={caseData.profile.name} />
              <Field
                label="Needle"
                value={`${caseData.profile.needle_gauge ?? "—"}${caseData.profile.needle_id_um ? ` · ${caseData.profile.needle_id_um} µm` : ""}`}
              />
              <Field
                label="Set pressure / time"
                value={`${caseData.profile.set_pressure_kpa ?? "—"} kPa / ${caseData.profile.set_time_ms ?? "—"} ms`}
              />
              <Field
                label="Spec"
                value={
                  caseData.profile.spec_metric && caseData.profile.spec_limit
                    ? `${caseData.profile.spec_metric} ${caseData.profile.spec_limit}`
                    : "—"
                }
              />
              <Field label="Rules version" value={caseData.rules_version} />
              <Link
                href={`/profiles/${caseData.profile.profile_id}?caseId=${caseData.case_id}`}
                className="inline-flex items-center gap-1 text-xs font-medium text-sky-600 hover:underline dark:text-sky-400"
              >
                <Compass className="size-3.5" />
                Pattern geometry
              </Link>
            </CardContent>
          </Card>
        </div>

        {caseData.complaint_text && (
          <div className="space-y-1">
            <h2 className="text-sm font-medium">Complaint, in their words</h2>
            <p className="text-sm text-muted-foreground">{caseData.complaint_text}</p>
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-baseline justify-between gap-2">
            <h2 className="text-sm font-medium">Troubleshooting loop</h2>
            {/* Changes and observations are counted separately: only
                changes bear on whether this case could close CONFIRMED. */}
            <span className="text-xs text-muted-foreground">
              {caseData.action_count} change{caseData.action_count === 1 ? "" : "s"} &middot;{" "}
              {caseData.observation_count} looked
            </span>
          </div>
          {caseData.check_results.length === 0 ? (
            <p className="text-sm text-muted-foreground">No checks logged yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">#</TableHead>
                  <TableHead>Check</TableHead>
                  <TableHead>Kind</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>Detail</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {caseData.check_results.map((check) => (
                  <TableRow key={check.check_result_id}>
                    <TableCell>{check.sequence}</TableCell>
                    <TableCell className="font-medium whitespace-normal">{check.check_name}</TableCell>
                    <TableCell className="text-muted-foreground">{check.is_change ? "changed" : "looked"}</TableCell>
                    <TableCell>
                      {check.outcome ? (
                        <Badge variant={OUTCOME_VARIANT[check.outcome]}>{check.outcome.replaceAll("_", " ")}</Badge>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="whitespace-normal text-muted-foreground">{check.result_detail ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>

        </TabsContent>

        <TabsContent value="artifacts">
          <ArtifactPanel artifacts={artifacts} flat />
        </TabsContent>
      </Tabs>
    </details>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium text-foreground">{value}</div>
    </div>
  );
}
