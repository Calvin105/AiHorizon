"use client";

import * as React from "react";
import { LifeBuoy, X } from "lucide-react";

import { EngineerNotes, markReviewed } from "@/components/engineer-notes";
import { Button } from "@/components/ui/button";
import type { Case } from "@/lib/api/types";

/**
 * The engineer's notes, without leaving the wizard. A senior engineer
 * answering a "Needs review" case logs the checks, re-measures and closes
 * here; this is where they answer the operator and mark it reviewed too,
 * rather than walking back to the case page to do it.
 */
export function NotesDrawer({
  caseData, open, onClose, onCaseChange,
}: {
  caseData: Case;
  open: boolean;
  onClose: () => void;
  onCaseChange: (updated: Case) => void;
}) {
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/30"
      role="dialog" aria-modal="true" aria-label="Engineer notes"
      onClick={onClose}
    >
      <div
        className="flex h-full w-full max-w-md flex-col gap-4 overflow-y-auto bg-background p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-base font-semibold">Case #{caseData.case_id} &middot; engineer notes</h2>
          <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        {caseData.escalate ? (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3">
            <p className="flex items-center gap-1.5 text-sm font-medium text-destructive">
              <LifeBuoy className="size-4" />
              An operator asked for help
            </p>
            <p className="mt-1 text-sm font-semibold">
              {caseData.escalation_note ? `“${caseData.escalation_note}”` : "No question given."}
            </p>
          </div>
        ) : caseData.escalation_note ? (
          <p className="text-sm text-muted-foreground">
            The operator asked: &ldquo;{caseData.escalation_note}&rdquo; &middot; reviewed
          </p>
        ) : null}

        <EngineerNotes
          caseId={caseData.case_id}
          initial={caseData.engineer_notes}
          onSaved={(notes) => onCaseChange({ ...caseData, engineer_notes: notes })}
          onMarkReviewed={
            caseData.escalate
              ? async (notes) => {
                  const updated = await markReviewed(caseData.case_id, notes);
                  if (updated) {
                    onCaseChange(updated);
                    onClose();
                  }
                }
              : undefined
          }
          placeholder={
            caseData.escalate
              ? "Answer the operator — what you found, what to do next. They see this the next time they open the case."
              : undefined
          }
        />
        <p className="text-xs text-muted-foreground">
          Notes print in section 8 of the report
          {caseData.escalate ? ", and the operator sees them the next time they open this case." : "."}
        </p>
      </div>
    </div>
  );
}
