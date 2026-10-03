import { apiRequest } from "@/lib/api/client";
import type { Ranking, RuleMap } from "@/lib/api/types";

export function rankCase(caseId: number) {
  return apiRequest<Ranking>(`/cases/${caseId}/rank`, { method: "POST" });
}

export function getRuleMap() {
  return apiRequest<RuleMap>("/rules");
}
