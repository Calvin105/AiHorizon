"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowRight,
  Compass,
  Database,
  Factory,
  FilePlus2,
  FolderOpen,
  History,
  LifeBuoy,
  type LucideIcon,
} from "lucide-react";

import { RuleMap } from "@/components/rule-map";
import { Skeleton } from "@/components/ui/skeleton";
import { TierInfo } from "@/components/tier-info";
import { ApiError } from "@/lib/api/client";
import { listCases } from "@/lib/api/cases";
import { listStations } from "@/lib/api/stations";
import type { Case, DispenseStation } from "@/lib/api/types";

/** An open case untouched this long is called out on the home page. A
 * shift is the unit people hand over in, so a day means it outlived one. */
const STALE_AFTER_MS = 24 * 60 * 60 * 1000;

interface HomeData {
  cases: Case[];
  stations: DispenseStation[];
  /** Captured when the data arrives, so "open for over a day" is worked
   * out against one clock instead of calling Date.now() during render. */
  loadedAt: number;
}

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

function plural(n: number, word: string) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/**
 * The home page is a status board, not a landing page: where the line
 * stands, what is waiting on someone, and every place to go from here, all
 * on one screen. Counts that need action sit on the tile that acts on them,
 * so the grid is both the menu and the to-do list. Beside it on a wide
 * screen, below it on a narrow one: the rule map every ranking is built from.
 */
export default function HomePage() {
  const [data, setData] = React.useState<HomeData | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    // 200 is the API's page cap. Past that, the counts below would be of
    // the newest 200 only and want a summary endpoint instead.
    Promise.all([listCases({ limit: 200 }), listStations({ limit: 50 })])
      .then(([cases, stations]) =>
        setData({ cases: cases.items, stations: stations.items, loadedAt: Date.now() }),
      )
      .catch((err: unknown) =>
        setError(err instanceof ApiError ? err.message : "Could not reach the API."),
      );
  }, []);

  const stats = React.useMemo(() => {
    if (!data) return null;
    const open = data.cases.filter((c) => !c.closed_at);
    const closed = data.cases.filter((c) => c.closed_at);
    // Oldest first: the one that has waited longest is the one to name.
    const byAge = (a: Case, b: Case) => a.opened_at.localeCompare(b.opened_at);
    return {
      open,
      closed,
      escalated: data.cases.filter((c) => c.escalate).sort(byAge),
      stale: open.filter((c) => data.loadedAt - Date.parse(c.opened_at) > STALE_AFTER_MS).sort(byAge),
      proven: closed.filter((c) => c.tier === "CONFIRMED").length,
      lastOpened: data.cases[0]?.opened_at ?? null,
    };
  }, [data]);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-10 min-[1240px]:grid min-[1240px]:max-w-[100rem] min-[1240px]:grid-cols-[26rem_minmax(0,1fr)] min-[1240px]:items-start min-[1240px]:gap-8">
      <div className="space-y-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">AI Dispensing Defect Detective</h1>
            <p className="text-xs text-muted-foreground">Dispensing troubleshooting for NSW Automation lines</p>
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
            How ranking works <TierInfo />
          </span>
        </div>

        {/* Where the line stands */}
        <section className="rounded-xl bg-muted/60 p-4 sm:p-5">
          {error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : !data || !stats ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-2/3" />
              <Skeleton className="h-4 w-full" />
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <LineIdentity stations={data.stations} />
                <dl className="grid grid-cols-3 gap-x-5 gap-y-1 text-sm sm:grid-cols-1 sm:text-right">
                  <Stat label="Open cases" value={stats.open.length} />
                  <Stat label="Closed cases" value={stats.closed.length} />
                  <Stat label="Last case" value={stats.lastOpened ? shortDate(stats.lastOpened) : "—"} />
                </dl>
              </div>
              <ProvenBar proven={stats.proven} closed={stats.closed.length} />
            </div>
          )}
        </section>

        {/* What is waiting on someone. Each line names the oldest case so the
            reader knows what they're walking into before they click. */}
        {stats && (
          <section className="space-y-2">
            {stats.escalated.length > 0 && (
              <Notice
                href="/cases?view=review"
                tone="urgent"
                text={
                  `${plural(stats.escalated.length, "case")} waiting for a senior engineer. ` +
                  `Oldest: #${stats.escalated[0].case_id}` +
                  (stats.escalated[0].escalation_note ? ` — "${stats.escalated[0].escalation_note}"` : "")
                }
              />
            )}
            {stats.stale.length > 0 && (
              <Notice
                href="/cases?view=open"
                tone="info"
                text={staleText(stats.stale)}
              />
            )}
            {stats.escalated.length === 0 && stats.stale.length === 0 && (
              <p className="px-1 text-sm text-muted-foreground">Nothing is waiting on anyone.</p>
            )}
          </section>
        )}

        {/* Actions. The one everyone comes here for is full width; the rest
            share the grid, and only work that's waiting gets a count. */}
        <nav className="grid grid-cols-2 gap-3" aria-label="Main actions">
          <Link
            href="/troubleshoot"
            className="group col-span-2 flex items-center gap-4 rounded-xl bg-primary p-4 text-primary-foreground shadow-sm transition-opacity hover:opacity-90 sm:p-5"
          >
            <span className="flex size-11 shrink-0 items-center justify-center rounded-lg bg-primary-foreground/15">
              <FilePlus2 className="size-5" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-base font-semibold">Troubleshoot a new case</span>
              <span className="block text-sm opacity-80">Photo, five questions, ranked causes, what to check first</span>
            </span>
            <ArrowRight className="size-5 shrink-0 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Tile
            href="/cases?view=review"
            icon={LifeBuoy}
            label="Needs review"
            hint="Cases an operator escalated"
            count={stats?.escalated.length}
            tone="urgent"
          />
          <Tile
            href="/cases?view=open"
            icon={FolderOpen}
            label="Open cases"
            hint="Pick up where someone left off"
            count={stats?.open.length}
            tone="info"
          />
          <Tile href="/cases" icon={History} label="Past cases" hint="Every case and how it closed" />
          <Tile href="/profiles" icon={Compass} label="Dispense profiles" hint="Nominal specs and patterns" />
        </nav>

        {/* Setup, kept apart from the day-to-day actions above. */}
        <div className="flex justify-center border-t pt-4">
          <Link
            href="/catalog"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
          >
            <Database className="size-4" />
            Stations, materials and profiles setup
          </Link>
        </div>
      </div>

      <RuleMap className="mt-10 min-[1240px]:mt-0" />
    </div>
  );
}

function staleText(stale: Case[]) {
  const noChecks = stale.filter((c) => c.check_results.length === 0).length;
  const checkNote =
    noChecks === stale.length
      ? stale.length === 1 ? " No check recorded yet." : " None has a check recorded."
      : noChecks > 0 ? ` ${noChecks} with no check recorded.` : "";
  return `${plural(stale.length, "case")} open since ${shortDate(stale[0].opened_at)}.${checkNote}`;
}

function LineIdentity({ stations }: { stations: DispenseStation[] }) {
  const only = stations.length === 1 ? stations[0] : null;
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-background">
        <Factory className="size-6" />
      </span>
      <div className="min-w-0">
        {only ? (
          <>
            <p className="font-semibold">
              {only.name} &middot; {only.line}
            </p>
            <p className="text-sm text-muted-foreground">
              {only.dispenser_class.replaceAll("_", "-")}
              {only.camera_available ? " · camera on" : " · no camera"}
            </p>
          </>
        ) : (
          <>
            <p className="font-semibold">{plural(stations.length, "station")}</p>
            <p className="text-sm text-muted-foreground">
              {stations.length > 0
                ? [...new Set(stations.map((s) => s.line))].join(", ")
                : "Add one in setup before opening a case"}
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-end sm:gap-4">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-semibold tabular-nums sm:min-w-14">{value}</dd>
    </div>
  );
}

/** Only CONFIRMED cases feed the ranking (Gate B), so the split that
 * matters is proven against everything else. */
function ProvenBar({ proven, closed }: { proven: number; closed: number }) {
  const pct = closed > 0 ? (proven / closed) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div
        className="flex h-2.5 overflow-hidden rounded-full bg-background"
        role="img"
        aria-label={`${proven} of ${closed} closed cases proven`}
      >
        <div className="bg-primary" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-sm">
        <span className="font-medium">{proven} proven fix{proven === 1 ? "" : "es"}</span>
        <span className="text-muted-foreground"> &middot; {closed - proven} unproven</span>
      </p>
    </div>
  );
}

function Notice({ href, tone, text }: { href: string; tone: "urgent" | "info"; text: string }) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm transition-colors ${
        tone === "urgent"
          ? "bg-destructive/10 hover:bg-destructive/15"
          : "bg-muted/60 hover:bg-muted"
      }`}
    >
      <span
        className={`size-2 shrink-0 rounded-full ${tone === "urgent" ? "bg-destructive" : "bg-muted-foreground"}`}
        aria-hidden
      />
      <span className="min-w-0 flex-1 line-clamp-2">{text}</span>
      <span className="inline-flex shrink-0 items-center gap-1 font-medium">
        Review <ArrowRight className="size-3.5" />
      </span>
    </Link>
  );
}

function Tile({
  href, icon: Icon, label, hint, count, tone,
}: {
  href: string;
  icon: LucideIcon;
  label: string;
  hint: string;
  count?: number;
  tone?: "urgent" | "info";
}) {
  return (
    <Link
      href={href}
      className="relative flex items-center gap-3 rounded-xl bg-muted/60 p-3 transition-colors hover:bg-muted sm:p-4"
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-background">
        <Icon className="size-5" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm leading-tight font-medium sm:text-base">{label}</span>
        <span className="hidden truncate text-xs text-muted-foreground sm:block">{hint}</span>
      </span>
      {/* A zero is no badge at all: a badge that is always there stops
          meaning anything. */}
      {count ? (
        <span
          className={`absolute -top-2 -right-2 flex h-6 min-w-6 items-center justify-center rounded-full px-1.5 text-xs font-semibold tabular-nums shadow-sm ${
            tone === "urgent" ? "bg-destructive text-white" : "bg-foreground text-background"
          }`}
        >
          {count}
          <span className="sr-only"> waiting</span>
        </span>
      ) : null}
    </Link>
  );
}
