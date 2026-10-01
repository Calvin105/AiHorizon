import { apiRequest } from "@/lib/api/client";
import type { MapFreeTextResponse, NextFollowUp, Question } from "@/lib/api/types";

export function getIntakeSpec() {
  return apiRequest<Question[]>("/intake/spec");
}

export function mapFreeText(data: { case_id: number; question_id: string; text: string }) {
  return apiRequest<MapFreeTextResponse>("/intake/map", { method: "POST", body: data });
}

/** Every adaptive follow-up question — for labelling answers already on file. */
export function getFollowupBank() {
  return apiRequest<Question[]>("/intake/followups");
}

/** The follow-up worth asking next for this case, or null when none would
 * move the ranking (or two have been asked already). */
export function getNextFollowup(caseId: number) {
  return apiRequest<NextFollowUp | null>("/intake/followups/next", { searchParams: { case_id: caseId } });
}
