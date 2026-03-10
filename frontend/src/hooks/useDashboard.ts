/**
 * React Query hook for fetching dashboard metrics.
 */
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";
import type { DashboardData } from "../types";

export function useDashboard() {
  return useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const response = await apiClient.get("/reports/dashboard/");
      return response.data;
    },
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}

export interface AssetSummaryReport {
  generated_at: string;
  total_assets: number;
  status_breakdown: Record<string, number>;
  condition_breakdown: Record<string, number>;
  financials: {
    total_purchase_cost: string;
    average_purchase_cost: string;
    total_salvage_value: string;
  };
  by_category: Array<{
    category: string;
    count: number;
    total_cost: string;
  }>;
}

export function useAssetSummaryReport() {
  return useQuery<AssetSummaryReport>({
    queryKey: ["reports", "asset-summary"],
    queryFn: async () => {
      const response = await apiClient.get("/reports/asset-summary/");
      return response.data;
    },
    staleTime: 5 * 60_000,
  });
}

export interface LicenseComplianceReport {
  generated_at: string;
  total_licenses: number;
  active: number;
  expired: number;
  compliance_rate: number;
  total_annual_cost: string;
  total_purchase_cost: string;
  over_utilized_licenses: Array<{
    id: string;
    software_name: string;
    total_seats: number;
    used_seats: number;
    utilization: number;
  }>;
  under_utilized_licenses: Array<{
    id: string;
    software_name: string;
    total_seats: number;
    used_seats: number;
    utilization: number;
  }>;
  expiring_within_30_days: number;
}

export function useLicenseComplianceReport() {
  return useQuery<LicenseComplianceReport>({
    queryKey: ["reports", "license-compliance"],
    queryFn: async () => {
      const response = await apiClient.get("/reports/license-compliance/");
      return response.data;
    },
    staleTime: 5 * 60_000,
  });
}
