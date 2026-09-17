"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { ArtifactPanel, type Artifacts } from "@/components/wizard/artifact-panel";
import { ChatPanel } from "@/components/wizard/chat-panel";
import { nextId, type ChatMessage, type ChipOption, type PendingPrompt } from "@/components/wizard/chat-types";
import { Skeleton } from "@/components/ui/skeleton";
import { apiRequest, ApiError } from "@/lib/api/client";
import { createCheckResult, getCase } from "@/lib/api/cases";
import { updateCase } from "@/lib/api/cases";
import { getIntakeSpec } from "@/lib/api/intake";
import { rankCase } from "@/lib/api/ranking";
import { closeCase, getReport, verifyCase } from "@/lib/api/report";
import { analysePhoto } from "@/lib/api/vision";
import type { Case, CoarseMatch, Fingerprint, FingerprintAxes, Question } from "@/lib/api/types";

type StepId =
  | "intro" | "ask_signature" | "ask_trajectory" | "ask_footprint" | "ask_inputs" | "ask_response"
  | "save_fingerprint" | "ask_photo" | "retrieve_coarse" | "rank" | "loop_prompt"
  | "loop_check_name" | "loop_check_cause" | "loop_check_outcome" | "loop_check_detail" | "loop_submit"
  | "report" | "verify_prompt" | "verify_photo" | "close_prompt" | "close" | "done";

function toChips(q: Question): ChipOption[] {
  return q.options.map((o) => ({ value: o.value, label: o.value.replaceAll("_", " "), helpText: o.help_text }));
}

export default function CaseWizardPage() {
  const params = useParams<{ id: string }>();
  const caseId = Number(params.id);

  const [loading, setLoading] = React.useState(true);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [pending, setPending] = React.useState<PendingPrompt>({ kind: "none" });
  const [busy, setBusy] = React.useState(false);
  const [artifacts, setArtifacts] = React.useState<Artifacts | null>(null);

  const questionsRef = React.useRef<Question[]>([]);
  const axesRef = React.useRef<Partial<FingerprintAxes>>({});
  const draftCheckRef = React.useRef<{ check_name?: string; cause_id?: string; outcome?: string }>({});
  const artifactsRef = React.useRef<Artifacts | null>(null);
  const currentStepRef = React.useRef<StepId>("intro");

  function say(text: string) {
    setMessages((prev) => [...prev, { id: nextId(), role: "bot", text }]);
  }
  function echo(text: string) {
    setMessages((prev) => [...prev, { id: nextId(), role: "user", text }]);
  }
  function patchArtifacts(patch: Partial<Artifacts>) {
    setArtifacts((prev) => {
      if (!prev) return prev;
      const next = { ...prev, ...patch };
      artifactsRef.current = next;
      return next;
    });
  }

  async function runStep(step: StepId, caseData: Case, arg?: unknown) {
    currentStepRef.current = step;
    switch (step) {
      case "intro": {
        say(
          `Opened case #${caseData.case_id} on ${caseData.station.name}, running ${caseData.profile.name} ` +
            `(${caseData.profile.material.name}). Let's find out what's wrong.`,
        );
        return runStep("ask_signature", caseData);
      }

      case "ask_signature": {
        const q = questionsRef.current.find((x) => x.id === "signature")!;
        say(q.prompt);
        setPending({ kind: "chips-multi", options: toChips(q), maxPicks: q.max_picks ?? undefined, confirmLabel: "Confirm" });
        return;
      }
      case "ask_trajectory": {
        const q = questionsRef.current.find((x) => x.id === "trajectory")!;
        say(q.prompt);
        setPending({ kind: "chips-single", options: toChips(q) });
        return;
      }
      case "ask_footprint": {
        const q = questionsRef.current.find((x) => x.id === "footprint")!;
        say(q.prompt);
        setPending({ kind: "chips-single", options: toChips(q) });
        return;
      }
      case "ask_inputs": {
        const q = questionsRef.current.find((x) => x.id === "inputs")!;
        say(q.prompt);
        setPending({ kind: "chips-multi", options: toChips(q), confirmLabel: "Confirm" });
        return;
      }
      case "ask_response": {
        const q = questionsRef.current.find((x) => x.id === "response")!;
        say(q.prompt);
        setPending({ kind: "chips-single", options: toChips(q) });
        return;
      }

      case "save_fingerprint": {
        setBusy(true);
        try {
          const fingerprint: Fingerprint = {
            axes: {
              signature: axesRef.current.signature ?? [],
              trajectory: axesRef.current.trajectory ?? null,
              footprint: axesRef.current.footprint ?? null,
              inputs: axesRef.current.inputs ?? [],
              response: axesRef.current.response ?? null,
            },
            signals: {},
          };
          await updateCase(caseData.case_id, { fingerprint });
          patchArtifacts({ axes: { ...axesRef.current } });
          say("Recorded. Want to attach a photo of the deposits? It sharpens the ranking, but it's optional.");
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not save the answers.");
        } finally {
          setBusy(false);
        }
        currentStepRef.current = "ask_photo";
        setPending({ kind: "photo-or-skip", skipLabel: "Skip — no photo" });
        return;
      }

      case "ask_photo": {
        const file = arg as File;
        setBusy(true);
        try {
          const url = URL.createObjectURL(file);
          patchArtifacts({ photoUrl: url });
          echo(`[attached ${file.name}]`);
          say("Analysing…");
          const vision = await analysePhoto(caseData.case_id, file);
          patchArtifacts({ vision });
          say(
            vision.quality_ok
              ? `Measured it — magnitude looks ${vision.magnitude}.`
              : `Couldn't measure it reliably: ${vision.quality_reason} Continuing on the answers alone.`,
          );
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not analyse the photo.");
        } finally {
          setBusy(false);
        }
        return runStep("retrieve_coarse", caseData);
      }

      case "retrieve_coarse": {
        setBusy(true);
        try {
          const matches = await apiRequest<CoarseMatch[]>(`/cases/${caseData.case_id}/retrieval/coarse`);
          patchArtifacts({ coarse: matches });
          say(
            matches.length === 0
              ? "No similar past cases on file yet."
              : `Found ${matches.length} similar past case(s) — pre-loading likely checks.`,
          );
        } catch {
          patchArtifacts({ coarse: [] });
        } finally {
          setBusy(false);
        }
        return runStep("rank", caseData);
      }

      case "rank": {
        setBusy(true);
        say("Ranking causes…");
        try {
          const ranking = await rankCase(caseData.case_id);
          patchArtifacts({ ranking });
          const top = ranking.pass1[0];
          say(
            ranking.tier === "T4"
              ? "No lead cause — pass 1 and pass 2 disagree and no signal breaks the tie. Let's troubleshoot to find out."
              : `Tier ${ranking.tier}. Top candidate: ${top.label} at ${Math.round(top.likelihood * 100)}%.`,
          );
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not rank causes.");
        } finally {
          setBusy(false);
        }
        return runStep("loop_prompt", caseData);
      }

      case "loop_prompt": {
        say("Want to log a troubleshooting check, or move on to the report?");
        setPending({
          kind: "confirm",
          options: [{ value: "log", label: "Log a check" }, { value: "report", label: "Continue to report" }],
        });
        return;
      }

      case "loop_check_name": {
        say("What did you try?");
        setPending({ kind: "text", placeholder: "e.g. purge and re-prime", confirmLabel: "Next" });
        return;
      }
      case "loop_check_cause": {
        const ranking = artifactsRef.current?.ranking;
        const options: ChipOption[] = (ranking?.pass1 ?? []).slice(0, 4).map((c) => ({ value: c.cause_id, label: c.label }));
        say("Which candidate cause does that test?");
        setPending({ kind: "chips-single", options });
        return;
      }
      case "loop_check_outcome": {
        say("What happened?");
        setPending({
          kind: "chips-single",
          options: [
            { value: "confirms", label: "Confirms it" },
            { value: "rules_out", label: "Rules it out" },
            { value: "inconclusive", label: "Inconclusive" },
          ],
        });
        return;
      }
      case "loop_check_detail": {
        say("Any detail worth recording? (optional)");
        setPending({ kind: "text", placeholder: "e.g. air slug expelled", confirmLabel: "Log it", allowEmpty: true });
        return;
      }
      case "loop_submit": {
        setBusy(true);
        try {
          const detail = arg as string;
          const updated = await createCheckResult(caseData.case_id, {
            check_name: draftCheckRef.current.check_name!,
            cause_id: draftCheckRef.current.cause_id!,
            cost_minutes: null, invasive: false, safety_note: null,
            outcome: draftCheckRef.current.outcome as "confirms" | "rules_out" | "inconclusive",
            result_detail: detail || null,
          });
          const refreshed = await getCase(caseData.case_id);
          patchArtifacts({ ranking: updated, checks: refreshed.check_results });
          say(`Logged — re-ranked. Top candidate now: ${updated.pass1[0].label} at ${Math.round(updated.pass1[0].likelihood * 100)}%.`);
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not log the check.");
        } finally {
          setBusy(false);
          draftCheckRef.current = {};
        }
        return runStep("loop_prompt", caseData);
      }

      case "report": {
        setBusy(true);
        say("Compiling the report…");
        try {
          const report = await getReport(caseData.case_id, true);
          patchArtifacts({ report });
          say(report.explanation ?? "Report ready — see the panel.");
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not compile the report.");
        } finally {
          setBusy(false);
        }
        currentStepRef.current = "verify_prompt";
        say("Want to verify the fix with a fresh photo?");
        setPending({ kind: "photo-or-skip", skipLabel: "Skip verification" });
        return;
      }

      case "verify_photo": {
        const file = arg as File;
        setBusy(true);
        try {
          const verification = await verifyCase(caseData.case_id, file, 30);
          const currentReport = artifactsRef.current?.report ?? null;
          patchArtifacts({ report: currentReport ? { ...currentReport, verification } : currentReport });
          say(
            verification.in_spec
              ? `Re-measured: ${verification.before ?? "—"} → ${verification.after ?? "—"}, back in spec.`
              : `Re-measured: ${verification.before ?? "—"} → ${verification.after ?? "—"}, still not in spec.`,
          );
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not verify.");
        } finally {
          setBusy(false);
        }
        return runStep("close_prompt", caseData);
      }

      case "close_prompt": {
        say("Ready to close the case?");
        setPending({ kind: "confirm", options: [{ value: "close", label: "Close the case" }] });
        return;
      }
      case "close": {
        setBusy(true);
        try {
          const result = await closeCase(caseData.case_id);
          patchArtifacts({ close: result });
          say(
            `Closed as ${result.tier}.` +
              (result.gaps.length > 0 ? ` Gaps: ${result.gaps.join("; ")}.` : " Every condition was met."),
          );
        } catch (err) {
          toast.error(err instanceof ApiError ? err.message : "Could not close the case.");
        } finally {
          setBusy(false);
        }
        currentStepRef.current = "done";
        setPending({ kind: "none" });
        return;
      }

      default:
        return;
    }
  }

  React.useEffect(() => {
    let cancelled = false;
    Promise.all([getCase(caseId), getIntakeSpec()])
      .then(([caseData, questions]) => {
        if (cancelled) return;
        questionsRef.current = questions;
        const initial: Artifacts = {
          caseData, photoUrl: null, axes: {}, vision: null, coarse: null,
          ranking: null, comparison: null, checks: caseData.check_results, report: null, close: null,
        };
        artifactsRef.current = initial;
        setArtifacts(initial);
        setLoading(false);
        void runStep("intro", caseData);
      })
      .catch((err) => toast.error(err instanceof ApiError ? err.message : "Could not load the case."));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  function requireCase(): Case | null {
    return artifactsRef.current?.caseData ?? null;
  }

  function handleChipSingle(value: string) {
    const caseData = requireCase();
    if (!caseData) return;
    const step = currentStepRef.current;

    if (step === "ask_trajectory") { axesRef.current.trajectory = value; echo(labelFor("trajectory", value)); void runStep("ask_footprint", caseData); return; }
    if (step === "ask_footprint") { axesRef.current.footprint = value; echo(labelFor("footprint", value)); void runStep("ask_inputs", caseData); return; }
    if (step === "ask_response") { axesRef.current.response = value; echo(labelFor("response", value)); void runStep("save_fingerprint", caseData); return; }
    if (step === "loop_prompt") {
      echo(value === "log" ? "Log a check" : "Continue to report");
      void runStep(value === "log" ? "loop_check_name" : "report", caseData);
      return;
    }
    if (step === "loop_check_cause") {
      draftCheckRef.current.cause_id = value;
      const label = artifactsRef.current?.ranking?.pass1.find((c) => c.cause_id === value)?.label ?? value;
      echo(label);
      void runStep("loop_check_outcome", caseData);
      return;
    }
    if (step === "loop_check_outcome") {
      draftCheckRef.current.outcome = value;
      echo(value.replaceAll("_", " "));
      void runStep("loop_check_detail", caseData);
      return;
    }
    if (step === "close_prompt") {
      echo("Close the case");
      void runStep("close", caseData);
      return;
    }
  }

  function handleChipsMulti(values: string[]) {
    const caseData = requireCase();
    if (!caseData) return;
    const step = currentStepRef.current;

    if (step === "ask_signature") {
      axesRef.current.signature = values;
      echo(values.map((v) => labelFor("signature", v)).join(", "));
      void runStep("ask_trajectory", caseData);
      return;
    }
    if (step === "ask_inputs") {
      axesRef.current.inputs = values;
      echo(values.map((v) => labelFor("inputs", v)).join(", "));
      void runStep("ask_response", caseData);
      return;
    }
  }

  function handleText(value: string) {
    const caseData = requireCase();
    if (!caseData) return;
    const step = currentStepRef.current;

    if (step === "loop_check_name") {
      draftCheckRef.current.check_name = value;
      echo(value);
      void runStep("loop_check_cause", caseData);
      return;
    }
    if (step === "loop_check_detail") {
      echo(value || "(no detail)");
      void runStep("loop_submit", caseData, value);
      return;
    }
  }

  function handlePhoto(file: File) {
    const caseData = requireCase();
    if (!caseData) return;
    const step = currentStepRef.current;
    if (step === "ask_photo") void runStep("ask_photo", caseData, file);
    if (step === "verify_prompt") void runStep("verify_photo", caseData, file);
  }

  function handleSkip() {
    const caseData = requireCase();
    if (!caseData) return;
    const step = currentStepRef.current;
    if (step === "verify_prompt") {
      echo("Skip verification");
      void runStep("close_prompt", caseData);
    } else {
      echo("Skip — no photo");
      void runStep("retrieve_coarse", caseData);
    }
  }

  function labelFor(axisId: string, value: string): string {
    const q = questionsRef.current.find((x) => x.id === axisId);
    return q?.options.find((o) => o.value === value)?.value.replaceAll("_", " ") ?? value;
  }

  if (loading || !artifacts) {
    return (
      <div className="mx-auto max-w-5xl flex-1 space-y-3 px-6 py-10">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="grid flex-1 grid-cols-1 divide-x md:grid-cols-2" style={{ height: "100vh" }}>
      <ChatPanel
        messages={messages} pending={pending} busy={busy}
        onChipSingle={handleChipSingle} onChipsMulti={handleChipsMulti}
        onText={handleText} onPhoto={handlePhoto} onSkip={handleSkip}
      />
      <ArtifactPanel artifacts={artifacts} />
    </div>
  );
}
