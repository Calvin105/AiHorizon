"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, FilePlus2 } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { CasesTable } from "@/components/cases-table";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError } from "@/lib/api/client";
import { listCases } from "@/lib/api/cases";
import type { Case } from "@/lib/api/types";

/** `?view=` values. The home page's tiles and notices link straight to
 * the open and review lists, so the filter lives in the URL. */
type View = "all" | "open" | "review";

const VIEWS: Record<View, { title: string; empty: string; match: (c: Case) => boolean }> = {
  all: {
    title: "Past cases",
    empty: "No cases yet. Open one from the home page to get started.",
    match: () => true,
  },
  open: {
    title: "Open cases",
    empty: "No open cases. Everything on file has been closed.",
    match: (c) => !c.closed_at,
  },
  review: {
    title: "Needs review",
    empty: "Nobody is waiting on a review.",
    match: (c) => c.escalate,
  },
};

function toView(value: string | null): View {
  return value === "open" || value === "review" ? value : "all";
}

export default function CasesPage() {
  // useSearchParams needs a Suspense boundary above it, or the production
  // build fails prerendering this page.
  return (
    <React.Suspense fallback={null}>
      <CasesView />
    </React.Suspense>
  );
}

function CasesView() {
  const router = useRouter();
  const pathname = usePathname();
  const view = toView(useSearchParams().get("view"));

  const [cases, setCases] = React.useState<Case[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const controller = new AbortController();
    listCases({ limit: 200, offset: 0 })
      .then((page) => setCases(page.items))
      .catch((err: unknown) => {
        if (err instanceof ApiError) setError(err.message);
        else if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError("Could not reach the API.");
        }
      });
    return () => controller.abort();
  }, []);

  const { title, empty, match } = VIEWS[view];
  const shown = cases?.filter(match) ?? null;
  const count = (v: View) => (cases ? cases.filter(VIEWS[v].match).length : null);

  function setView(next: View) {
    router.replace(next === "all" ? pathname : `${pathname}?view=${next}`, { scroll: false });
  }

  return (
    <div className="mx-auto w-full max-w-[1520px] px-4 py-8 sm:px-6 lg:px-8 xl:px-12">
      <div className="mb-6 flex items-center justify-between">
        <Link
          href="/"
          className={buttonVariants({
            variant: "ghost",
            size: "sm",
            className: "gap-1.5 text-muted-foreground hover:text-foreground",
          })}
        >
          <ArrowLeft className="size-4" />
          Back to Home
        </Link>
        <Link
          href="/troubleshoot"
          className={buttonVariants({ size: "sm", className: "gap-1.5" })}
        >
          <FilePlus2 className="size-4" />
          Open New Case
        </Link>
      </div>

      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="mb-1 text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="text-sm text-muted-foreground">
            {shown
              ? `${shown.length} case${shown.length === 1 ? "" : "s"}${view === "all" ? " on file" : ""}.`
              : "Loading..."}
          </p>
        </div>
        <Tabs value={view} onValueChange={(v) => setView(toView(String(v)))}>
          <TabsList>
            {(["all", "open", "review"] as const).map((v) => (
              <TabsTrigger key={v} value={v} className="px-3">
                {v === "all" ? "All" : VIEWS[v].title}
                {count(v) != null && (
                  <span className="text-xs tabular-nums text-muted-foreground">{count(v)}</span>
                )}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {!error && !shown && (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-11 w-full" />
          ))}
        </div>
      )}

      {!error && shown && shown.length === 0 && (
        <p className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">
          {empty}
        </p>
      )}

      {!error && shown && shown.length > 0 && <CasesTable data={shown} />}
    </div>
  );
}
