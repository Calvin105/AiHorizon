import { apiRequest } from "@/lib/api/client";
import type { FluidMaterial, Page } from "@/lib/api/types";

export function listMaterials(params?: { limit?: number }) {
  return apiRequest<Page<FluidMaterial>>("/materials", { searchParams: params });
}
