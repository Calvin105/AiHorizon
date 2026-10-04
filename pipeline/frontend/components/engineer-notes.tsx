"use client";

import * as React from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api/client";
import { updateCase } from "@/lib/api/cases";
import type { Case } from "@/lib/api/types";

/** Clears the escalation, saving the reply with it so an unsaved reply
 * can't be lost to it. Null when it failed — the toast has said why. */
export async function markReviewed(caseId: number, notes: string | null): Promise<Case | null> {
  try {
    const updated = await updateCase(caseId, { engineer_notes: notes, escalate: false });
    toast.success(
      notes
        ? "Marked reviewed. The operator sees your notes next time they open this case."
        : "Marked reviewed.",
    );
    return updated;
  } catch (err) {
    toast.error(err instanceof ApiError ? err.message : "Could not mark the case reviewed.");
    return null;
  }
}

/** The engineer's own words on the case. Saved explicitly rather than on
 * blur or on a timer: this is the field a human is held to, and a note
 * that saves itself halfway through a sentence is worse than one that
 * waits to be told. */
export function EngineerNotes({
  caseId, initial, onSaved, onMarkReviewed, placeholder,
}: {
  caseId: number;
  initial: string | null;
  onSaved: (notes: string | null) => void;
  /** Review mode: a second button that saves the draft and clears the
   * escalation in one go, so an unsaved reply can't be lost to it. */
  onMarkReviewed?: (notes: string | null) => Promise<void>;
  placeholder?: string;
}) {
  const [value, setValue] = React.useState(initial ?? "");
  const [saving, setSaving] = React.useState(false);
  const dirty = value.trim() !== (initial ?? "").trim();

  async function save() {
    setSaving(true);
    try {
      const notes = value.trim() || null;
      await updateCase(caseId, { engineer_notes: notes });
      onSaved(notes);
      toast.success("Engineer notes saved.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not save the notes.");
    } finally {
      setSaving(false);
    }
  }

  async function markReviewedNow() {
    if (!onMarkReviewed) return;
    setSaving(true);
    try {
      await onMarkReviewed(value.trim() || null);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2">
        <h2 className="text-sm font-medium">Engineer notes</h2>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant={dirty && !onMarkReviewed ? "default" : "outline"}
            disabled={!dirty || saving}
            onClick={save}
          >
            {saving ? "Saving…" : "Save notes"}
          </Button>
          {onMarkReviewed && (
            <Button size="sm" disabled={saving} onClick={markReviewedNow}>
              Mark reviewed
            </Button>
          )}
        </div>
      </div>
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={
          placeholder ??
          "Anything the next person on this machine should know — what you saw, what you ruled out, what you'd try next."
        }
        className="min-h-24 text-sm"
      />
    </div>
  );
}
