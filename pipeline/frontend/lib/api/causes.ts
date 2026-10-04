import { apiRequest } from "@/lib/api/client";
import type { CauseComparison, CauseVocab, CheckStep } from "@/lib/api/types";

export function listCauses() {
  return apiRequest<CauseVocab[]>("/causes");
}

export function compareCauses(caseId: number) {
  return apiRequest<CauseComparison[]>(`/cases/${caseId}/compare`);
}

/** Every cause's troubleshooting plan, keyed by cause id. */
export function getCheckPlans() {
  return apiRequest<Record<string, CheckStep[]>>("/causes/checks");
}
