/**
 * Zustand store for asset-related UI state (filters, selection, view mode).
 * Data fetching is handled by React Query -- this store manages transient UI state only.
 */
import { create } from "zustand";
import type { AssetStatus, AssetCondition } from "../types";

interface AssetFilters {
  search: string;
  status: AssetStatus | "";
  condition: AssetCondition | "";
  category: string;
  asset_type: string;
  ordering: string;
  page: number;
  page_size: number;
}

interface AssetUIState {
  filters: AssetFilters;
  selectedAssetIds: Set<string>;
  viewMode: "table" | "grid";

  setFilter: <K extends keyof AssetFilters>(key: K, value: AssetFilters[K]) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  toggleAssetSelection: (id: string) => void;
  selectAllAssets: (ids: string[]) => void;
  clearSelection: () => void;
  setViewMode: (mode: "table" | "grid") => void;
}

const defaultFilters: AssetFilters = {
  search: "",
  status: "",
  condition: "",
  category: "",
  asset_type: "",
  ordering: "-created_at",
  page: 1,
  page_size: 25,
};

export const useAssetStore = create<AssetUIState>((set) => ({
  filters: { ...defaultFilters },
  selectedAssetIds: new Set(),
  viewMode: "table",

  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value, page: 1 },
    })),

  resetFilters: () =>
    set({ filters: { ...defaultFilters }, selectedAssetIds: new Set() }),

  setPage: (page) =>
    set((state) => ({
      filters: { ...state.filters, page },
    })),

  toggleAssetSelection: (id) =>
    set((state) => {
      const next = new Set(state.selectedAssetIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { selectedAssetIds: next };
    }),

  selectAllAssets: (ids) =>
    set({ selectedAssetIds: new Set(ids) }),

  clearSelection: () =>
    set({ selectedAssetIds: new Set() }),

  setViewMode: (mode) => set({ viewMode: mode }),
}));
