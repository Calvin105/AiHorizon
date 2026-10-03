import { apiRequest } from "@/lib/api/client";
import type { Ranking, RuleMap } from "@/lib/api/types";

export function rankCase(caseId: number) {
  return apiRequest<Ranking>(`/cases/${caseId}/rank`, { method: "POST" });
}

export function getRuleMap() {
  return apiRequest<RuleMap>("/rules");
}

/** Sets a rule's weight in force, with the reason. Returns the whole table. */
export function updateRule(key: string, body: { weight: number; note: string }) {
  return apiRequest<RuleMap>(`/rules/${encodeURIComponent(key)}`, { method: "PUT", body });
}

/** Back to the manual's weight. Returns the whole table. */
export function restoreRule(key: string) {
  return apiRequest<RuleMap>(`/rules/${encodeURIComponent(key)}`, { method: "DELETE" });
}
