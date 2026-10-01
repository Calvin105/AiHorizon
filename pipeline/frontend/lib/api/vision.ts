import { apiRequest } from "@/lib/api/client";
import type { VisionResult } from "@/lib/api/types";
import { preparePhoto } from "@/lib/photo";

export async function analysePhoto(caseId: number, photo: File) {
  const form = new FormData();
  form.set("photo", await preparePhoto(photo));
  return apiRequest<VisionResult>(`/cases/${caseId}/vision`, { method: "POST", formData: form });
}
