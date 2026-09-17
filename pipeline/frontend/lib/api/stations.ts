import { apiRequest } from "@/lib/api/client";
import type { DispenseStation, Page } from "@/lib/api/types";

export function listStations(params?: { limit?: number }) {
  return apiRequest<Page<DispenseStation>>("/stations", { searchParams: params });
}
