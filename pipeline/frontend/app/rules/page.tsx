"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, Grid3x3, LayoutList } from "lucide-react";

import { RuleList } from "@/components/rule-list";
import { RuleMap } from "@/components/rule-map";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApiError } from "@/lib/api/client";
import { getRuleMap } from "@/lib/api/ranking";
import type { RuleMap as RuleTable } from "@/lib/api/types";

/** `?view=` values: the list is for reading the rules, the map for trying
 * them. The list is the default — viewing comes first, editing second. */
type View = "list" | "map";

function toView(value: string | null): View {
  return value === "map" ? "map" : "list";
}

export default function RulesPage() {
  // useSearchParams needs a Suspense boundary above it, or the production
  // build fails prerendering this page.
  return (
    <React.Suspense fallback={null}>
      <RulesView />
    </React.Suspense>
  );
}

function RulesView() {
  const router = useRouter();
  const pathname = usePathname();
  const view = toView(useSearchParams().get("view"));

  const [table, setTable] = React.useState<RuleTable | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getRuleMap()
      .then(setTable)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : "Could not reach the API."));
  }, []);

  function setView(next: View) {
    router.replace(next === "list" ? pathname : `${pathname}?view=${next}`, { scroll: false });
  }

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
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
      </div>

      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div className="max-w-3xl">
          <h1 className="mb-1 text-2xl font-semibold tracking-tight">Ranking rules</h1>
          <p className="text-sm text-muted-foreground">
            Every percentage this system shows is built from {table ? `these ${table.rule_count}` : "these"} rules.
            Each cause starts at {table ? `${Math.round(table.prior * 100)}%` : "the same low odds"}; each rule says
            what it looks for, which cause it moves and by how much, and the page of the NPL guide or the NSW
            brief it comes from.
          </p>
        </div>
        <Tabs value={view} onValueChange={(v) => setView(toView(String(v)))}>
          <TabsList>
            <TabsTrigger value="list" className="gap-1.5 px-3">
              <LayoutList className="size-4" /> List
            </TabsTrigger>
            <TabsTrigger value="map" className="gap-1.5 px-3">
              <Grid3x3 className="size-4" /> Map
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : !table ? (
        <div className="space-y-3">
          <Skeleton className="h-9 w-80" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : view === "map" ? (
        <RuleMap table={table} />
      ) : (
        <RuleList table={table} onChange={setTable} />
      )}
    </div>
  );
}
