/**
 * React Query hooks for asset data fetching and mutations.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assetsApi, type AssetFilters } from "../api/assets";
import type { Asset, AssetListItem, PaginatedResponse } from "../types";

// ---- Query keys -------------------------------------------------------------

export const assetKeys = {
  all: ["assets"] as const,
  lists: () => [...assetKeys.all, "list"] as const,
  list: (filters: AssetFilters) => [...assetKeys.lists(), filters] as const,
  details: () => [...assetKeys.all, "detail"] as const,
  detail: (id: string) => [...assetKeys.details(), id] as const,
  statusSummary: () => [...assetKeys.all, "status-summary"] as const,
  categories: () => [...assetKeys.all, "categories"] as const,
  types: (categoryId?: string) => [...assetKeys.all, "types", categoryId] as const,
  assignments: (filters?: Record<string, unknown>) =>
    [...assetKeys.all, "assignments", filters] as const,
};

// ---- Queries ----------------------------------------------------------------

export function useAssetList(filters: AssetFilters = {}) {
  return useQuery<PaginatedResponse<AssetListItem>>({
    queryKey: assetKeys.list(filters),
    queryFn: () => assetsApi.list(filters),
    staleTime: 30_000,
  });
}

export function useAssetDetail(id: string) {
  return useQuery<Asset>({
    queryKey: assetKeys.detail(id),
    queryFn: () => assetsApi.get(id),
    enabled: !!id,
  });
}

export function useAssetStatusSummary() {
  return useQuery<Record<string, number>>({
    queryKey: assetKeys.statusSummary(),
    queryFn: () => assetsApi.statusSummary(),
    staleTime: 60_000,
  });
}

export function useAssetCategories() {
  return useQuery({
    queryKey: assetKeys.categories(),
    queryFn: () => assetsApi.listCategories(),
    staleTime: 5 * 60_000,
  });
}

export function useAssetTypes(categoryId?: string) {
  return useQuery({
    queryKey: assetKeys.types(categoryId),
    queryFn: () => assetsApi.listTypes(categoryId),
    staleTime: 5 * 60_000,
  });
}

// ---- Mutations --------------------------------------------------------------

export function useCreateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Asset>) => assetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: assetKeys.statusSummary() });
    },
  });
}

export function useUpdateAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Asset> }) =>
      assetsApi.update(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: assetKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => assetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: assetKeys.statusSummary() });
    },
  });
}

export function useCheckOutAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      assetId,
      data,
    }: {
      assetId: string;
      data: { employee: string; expected_return_date?: string; notes?: string };
    }) => assetsApi.checkOut(assetId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: assetKeys.detail(variables.assetId) });
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: assetKeys.statusSummary() });
    },
  });
}

export function useCheckInAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      assetId,
      data,
    }: {
      assetId: string;
      data: { condition?: string; notes?: string };
    }) => assetsApi.checkIn(assetId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: assetKeys.detail(variables.assetId) });
      queryClient.invalidateQueries({ queryKey: assetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: assetKeys.statusSummary() });
    },
  });
}
