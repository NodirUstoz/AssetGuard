/**
 * API service for asset-related endpoints.
 */
import apiClient from "./client";
import type {
  Asset,
  AssetListItem,
  AssetCategory,
  AssetType,
  AssetAssignment,
  PaginatedResponse,
} from "../types";

export interface AssetFilters {
  status?: string;
  condition?: string;
  asset_type?: string;
  category?: string;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const assetsApi = {
  // ---- Assets ---------------------------------------------------------------

  list(filters: AssetFilters = {}): Promise<PaginatedResponse<AssetListItem>> {
    return apiClient
      .get("/assets/", { params: filters })
      .then((res) => res.data);
  },

  get(id: string): Promise<Asset> {
    return apiClient.get(`/assets/${id}/`).then((res) => res.data);
  },

  create(data: Partial<Asset>): Promise<Asset> {
    return apiClient.post("/assets/", data).then((res) => res.data);
  },

  update(id: string, data: Partial<Asset>): Promise<Asset> {
    return apiClient.patch(`/assets/${id}/`, data).then((res) => res.data);
  },

  delete(id: string): Promise<void> {
    return apiClient.delete(`/assets/${id}/`);
  },

  checkOut(
    assetId: string,
    data: { employee: string; expected_return_date?: string; notes?: string },
  ): Promise<AssetAssignment> {
    return apiClient
      .post(`/assets/${assetId}/check-out/`, data)
      .then((res) => res.data);
  },

  checkIn(
    assetId: string,
    data: { condition?: string; notes?: string },
  ): Promise<AssetAssignment> {
    return apiClient
      .post(`/assets/${assetId}/check-in/`, data)
      .then((res) => res.data);
  },

  statusSummary(): Promise<Record<string, number>> {
    return apiClient
      .get("/assets/status-summary/")
      .then((res) => res.data);
  },

  getQrCodeUrl(assetId: string): string {
    return `${apiClient.defaults.baseURL}/assets/${assetId}/qr-code/`;
  },

  // ---- Categories -----------------------------------------------------------

  listCategories(): Promise<PaginatedResponse<AssetCategory>> {
    return apiClient
      .get("/assets/categories/")
      .then((res) => res.data);
  },

  createCategory(data: Partial<AssetCategory>): Promise<AssetCategory> {
    return apiClient
      .post("/assets/categories/", data)
      .then((res) => res.data);
  },

  // ---- Types ----------------------------------------------------------------

  listTypes(categoryId?: string): Promise<PaginatedResponse<AssetType>> {
    const params = categoryId ? { category: categoryId } : {};
    return apiClient
      .get("/assets/types/", { params })
      .then((res) => res.data);
  },

  createType(data: Partial<AssetType>): Promise<AssetType> {
    return apiClient
      .post("/assets/types/", data)
      .then((res) => res.data);
  },

  // ---- Assignments ----------------------------------------------------------

  listAssignments(
    filters: { asset?: string; employee?: string; is_active?: boolean } = {},
  ): Promise<PaginatedResponse<AssetAssignment>> {
    return apiClient
      .get("/assets/assignments/", { params: filters })
      .then((res) => res.data);
  },
};
