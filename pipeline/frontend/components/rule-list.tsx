"use client";

import * as React from "react";
import { Pencil, RotateCcw, Search, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { restoreRule, updateRule } from "@/lib/api/ranking";
import type { Rule, RuleMap as RuleTable } from "@/lib/api/types";
import { SHORT_NAMES, oddsEffect, ruleName, tone, weightText } from "@/lib/rules";
import { formatSource, formatWeight, plainDetail } from "@/lib/sources";
import { cn } from "@/lib/utils";

const WEIGHT_LIMIT = 5;
const MIN_NOTE = 3;

interface Trigger {
  title: string;
  labels: string[];
}

/** What fires a rule, grouped by the question it comes from:
 * "Q5 · What helps: Purging or priming, A new syringe". */
function triggersOf(rule: Rule, rows: Map<string, { title: string; label: string }>): Trigger[] {
  const out: Trigger[] = [];
  for (const id of rule.triggers) {
    const row = rows.get(id);
    if (!row) continue;
    const last = out[out.length - 1];
    if (last?.title === row.title) last.labels.push(row.label);
    else out.push({ title: row.title, labels: [row.label] });
  }
  return out;
}

/** Strongest evidence first; a measurement counts at its strongest reading. */
function strength(rule: Rule): number {
  return rule.full_strength ?? rule.weight;
}

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

/**
 * Every rule, grouped by the cause it moves. Reading them is the point;
 * changing one is a secondary action, and always leaves the manual's
 * weight and the reason on record.
 */
export function RuleList({ table, onChange }: { table: RuleTable; onChange: (next: RuleTable) => void }) {
  const [query, setQuery] = React.useState("");
  const [editing, setEditing] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const rows = React.useMemo(() => {
    const out = new Map<string, { title: string; label: string }>();
    for (const group of table.groups) {
      for (const row of group.rows) out.set(row.id, { title: group.title, label: row.label });
    }
    return out;
  }, [table]);

  const needle = query.trim().toLowerCase();
  const matches = (rule: Rule) =>
    !needle ||
    [
      rule.label, rule.detail, formatSource(rule.source), rule.note ?? "",
      table.causes.find((c) => c.cause_id === rule.cause_id)?.label ?? "",
      ...triggersOf(rule, rows).flatMap((t) => [t.title, ...t.labels]),
    ].some((text) => text.toLowerCase().includes(needle));

  const shown = table.rules.filter(matches);
  const edited = table.rules.filter((r) => r.weight !== r.manual_weight);

  async function run(action: () => Promise<RuleTable>) {
    setBusy(true);
    setError(null);
    try {
      onChange(await action());
      setEditing(null);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? JSON.stringify(err.body) : "Could not reach the API.");
    } finally {
      setBusy(false);
    }
  }

  async function restoreAll() {
    setBusy(true);
    setError(null);
    try {
      let latest = table;
      for (const rule of edited) latest = await restoreRule(rule.key);
      onChange(latest);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? JSON.stringify(err.body) : "Could not reach the API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by answer, cause or page"
            className="pl-8"
            aria-label="Filter rules"
          />
        </div>
        <p className="text-sm text-muted-foreground">
          {needle ? `${shown.length} of ${table.rules.length} rules` : `${table.rules.length} rules`}
        </p>
        {edited.length > 0 && (
          <p className="flex items-center gap-2 text-sm">
            <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-xs font-medium text-amber-900 dark:text-amber-200">
              {edited.length} edited
            </span>
            <span className="text-muted-foreground">from the manual&apos;s weights</span>
            <Button variant="ghost" size="xs" disabled={busy} onClick={restoreAll}>
              <RotateCcw /> Restore all
            </Button>
          </p>
        )}
      </div>
      {error && !editing && <p className="text-sm text-destructive">{error}</p>}

      {table.causes.map((cause) => {
        const rules = shown
          .filter((r) => r.cause_id === cause.cause_id)
          .sort((a, b) => strength(b) - strength(a));
        if (rules.length === 0) return null;
        const changed = rules.filter((r) => r.weight !== r.manual_weight).length;
        return (
          <section key={cause.cause_id} className="overflow-hidden rounded-xl border">
            <header className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5 bg-muted/60 px-4 py-2.5">
              <h2 className="font-medium">{cause.label}</h2>
              <span className="text-xs text-muted-foreground">
                {SHORT_NAMES[cause.cause_id] ? `${SHORT_NAMES[cause.cause_id]} · ` : ""}
                {needle ? `${rules.length} of ${cause.rule_count}` : cause.rule_count} rules
                {changed > 0 ? ` · ${changed} edited` : ""}
              </span>
            </header>
            <ul className="divide-y">
              {rules.map((rule) => (
                <RuleRow
                  key={rule.key}
                  rule={rule}
                  causeName={(SHORT_NAMES[rule.cause_id] ?? cause.label).toLowerCase()}
                  triggers={triggersOf(rule, rows)}
                  editing={editing === rule.key}
                  busy={busy}
                  error={editing === rule.key ? error : null}
                  onEdit={() => {
                    setEditing(rule.key);
                    setError(null);
                  }}
                  onCancel={() => setEditing(null)}
                  onSave={(weight, note) => run(() => updateRule(rule.key, { weight, note }))}
                  onRestore={() => run(() => restoreRule(rule.key))}
                />
              ))}
            </ul>
          </section>
        );
      })}
      {shown.length === 0 && (
        <p className="rounded-xl bg-muted/60 p-4 text-sm text-muted-foreground">No rule matches &ldquo;{query}&rdquo;.</p>
      )}
    </div>
  );
}

function RuleRow({
  rule, causeName, triggers, editing, busy, error, onEdit, onCancel, onSave, onRestore,
}: {
  rule: Rule;
  causeName: string;
  triggers: Trigger[];
  editing: boolean;
  busy: boolean;
  error: string | null;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (weight: number, note: string) => void;
  onRestore: () => void;
}) {
  const changed = rule.weight !== rule.manual_weight;
  return (
    <li className={cn("grid grid-cols-[4.25rem_minmax(0,1fr)] gap-x-3 px-4 py-3 sm:grid-cols-[4.25rem_minmax(0,1fr)_auto]", editing && "bg-muted/30")}>
      <div className="pt-0.5 text-center">
        <span className={cn("inline-block min-w-[3.25rem] rounded-md px-1.5 py-0.5 font-mono text-sm font-semibold tabular-nums", tone(rule.weight))}>
          {weightText(rule.weight)}
        </span>
        {rule.full_strength !== null && rule.weight !== 0 && (
          <span className="mt-1 flex items-center justify-center gap-0.5 text-[0.65rem] leading-tight text-muted-foreground" title="Grows with the reading">
            <TrendingUp className="size-3" /> up to {formatWeight(rule.full_strength)}
          </span>
        )}
      </div>

      <div className="min-w-0 space-y-1">
        <p className="text-sm leading-snug font-medium">
          {ruleName(rule.label)}
          {changed && (
            <span className="ml-2 rounded bg-amber-500/15 px-1.5 py-0.5 align-middle text-[0.65rem] font-medium text-amber-900 dark:text-amber-200">
              edited
            </span>
          )}
        </p>
        <p className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-xs text-foreground/80">
          {triggers.map((t, i) => (
            <React.Fragment key={t.title}>
              {i > 0 && <span className="text-muted-foreground">or</span>}
              <span className="rounded bg-muted px-1.5 py-0.5 text-[0.68rem] text-muted-foreground">{t.title}</span>
              <span>{t.labels.join(" · ")}</span>
            </React.Fragment>
          ))}
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">{plainDetail(rule.detail)}</p>
        {changed && (
          <p className="flex flex-wrap items-center gap-x-2 text-xs">
            <span className="text-muted-foreground">
              The manual gives {formatWeight(rule.manual_weight)}
              {rule.updated_at ? ` · changed ${shortDate(rule.updated_at)}` : ""}
              {rule.note ? `: “${rule.note}”` : ""}
            </span>
            {!editing && (
              <Button variant="ghost" size="xs" disabled={busy} onClick={onRestore}>
                <RotateCcw /> Restore
              </Button>
            )}
          </p>
        )}
        {editing && (
          <WeightEditor rule={rule} causeName={causeName} busy={busy} error={error} onCancel={onCancel} onSave={onSave} />
        )}
      </div>

      <div className="col-start-2 mt-1 flex items-center gap-1 sm:col-start-3 sm:mt-0 sm:flex-col sm:items-end sm:gap-1.5">
        <span className="text-xs whitespace-nowrap text-sky-700 italic dark:text-sky-400">{formatSource(rule.source)}</span>
        {!editing && (
          <Button
            variant="ghost"
            size="xs"
            className="text-muted-foreground"
            onClick={onEdit}
            aria-label={`Edit the weight of “${ruleName(rule.label)}”`}
          >
            <Pencil /> Edit
          </Button>
        )}
      </div>
    </li>
  );
}

function WeightEditor({
  rule, causeName, busy, error, onCancel, onSave,
}: {
  rule: Rule;
  causeName: string;
  busy: boolean;
  error: string | null;
  onCancel: () => void;
  onSave: (weight: number, note: string) => void;
}) {
  const [weight, setWeight] = React.useState(String(rule.weight));
  const [note, setNote] = React.useState(rule.note ?? "");
  const value = Number(weight);
  const weightOk = weight.trim() !== "" && Number.isFinite(value) && Math.abs(value) <= WEIGHT_LIMIT;
  const noteOk = note.trim().length >= MIN_NOTE;
  const id = `edit-${rule.key}`;

  return (
    <form
      className="mt-2 space-y-2.5 rounded-lg border bg-background p-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (weightOk && noteOk) onSave(value, note.trim());
      }}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <label htmlFor={`${id}-weight`} className="text-xs font-medium">
          Weight
        </label>
        <Input
          id={`${id}-weight`}
          type="number"
          step="0.1"
          min={-WEIGHT_LIMIT}
          max={WEIGHT_LIMIT}
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          className="h-8 w-24 font-mono"
          autoFocus
        />
        <span className="text-xs text-muted-foreground">
          {!weightOk
            ? `Between −${WEIGHT_LIMIT} and +${WEIGHT_LIMIT}.`
            : value === 0
              ? "0 switches the rule off."
              : `${formatWeight(value)} ${oddsEffect(value, causeName)}${rule.full_strength !== null ? " at strength 1" : ""}.`}
        </span>
      </div>
      <div className="space-y-1">
        <label htmlFor={`${id}-note`} className="text-xs font-medium">
          Why change it?
        </label>
        <Textarea
          id={`${id}-note`}
          rows={2}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="e.g. On our line this shows up mostly after a weekend shutdown"
          className="text-sm"
        />
      </div>
      <p className="text-[0.7rem] leading-relaxed text-muted-foreground">
        The manual gives {formatWeight(rule.manual_weight)} ({formatSource(rule.source)}). A change applies to every
        ranking from now on; cases already ranked keep their numbers until they are ranked again.
      </p>
      {error && <p className="text-xs text-destructive">{error}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={busy || !weightOk || !noteOk}>
          Save
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
