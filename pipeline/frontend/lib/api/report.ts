import { apiRequest } from "@/lib/api/client";
import type { CloseCaseResponse, Report, Verification } from "@/lib/api/types";
import { preparePhoto } from "@/lib/photo";

export function getReport(caseId: number, useLlmExplanation: boolean) {
  return apiRequest<Report>(`/cases/${caseId}/report`, {
    searchParams: { use_llm_explanation: useLlmExplanation },
  });
}

export async function verifyCase(caseId: number, photo: File, shotsMeasured: number) {
  const form = new FormData();
  form.set("photo", await preparePhoto(photo));
  form.set("shots_measured", String(shotsMeasured));
  return apiRequest<Verification>(`/cases/${caseId}/verify`, { method: "POST", formData: form });
}

export function closeCase(caseId: number) {
  return apiRequest<CloseCaseResponse>(`/cases/${caseId}/close`, { method: "POST" });
}

/** What closing now would record: the verdict and every condition still
 * unproved. Closes nothing. On a closed case, the gaps behind its verdict. */
export function previewClose(caseId: number) {
  return apiRequest<CloseCaseResponse>(`/cases/${caseId}/close`);
}
