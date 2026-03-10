/**
 * Formatting and display utilities for the AssetGuard frontend.
 */
import { format, formatDistanceToNow, parseISO, isValid } from "date-fns";

/**
 * Format an ISO date string into a human-readable date.
 * Returns "N/A" for null/undefined/invalid values.
 */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  const date = parseISO(dateStr);
  return isValid(date) ? format(date, "MMM d, yyyy") : "N/A";
}

/**
 * Format an ISO datetime string into a date + time.
 */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  const date = parseISO(dateStr);
  return isValid(date) ? format(date, "MMM d, yyyy h:mm a") : "N/A";
}

/**
 * Format a date string as a relative time (e.g., "3 days ago").
 */
export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "N/A";
  const date = parseISO(dateStr);
  return isValid(date) ? formatDistanceToNow(date, { addSuffix: true }) : "N/A";
}

/**
 * Format a number/string as currency (USD).
 */
export function formatCurrency(
  value: string | number | null | undefined,
): string {
  if (value === null || value === undefined) return "$0.00";
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

/**
 * Format a number as a percentage string.
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "0%";
  return `${value.toFixed(1)}%`;
}

/**
 * Map asset status values to user-friendly labels.
 */
export const STATUS_LABELS: Record<string, string> = {
  available: "Available",
  assigned: "Assigned",
  in_maintenance: "In Maintenance",
  retired: "Retired",
  disposed: "Disposed",
  lost: "Lost",
  damaged: "Damaged",
};

/**
 * Map asset condition values to user-friendly labels.
 */
export const CONDITION_LABELS: Record<string, string> = {
  new: "New",
  good: "Good",
  fair: "Fair",
  poor: "Poor",
  broken: "Broken",
};

/**
 * Map status to a Tailwind CSS color class for badges.
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    available: "bg-green-100 text-green-800",
    assigned: "bg-blue-100 text-blue-800",
    in_maintenance: "bg-yellow-100 text-yellow-800",
    retired: "bg-gray-100 text-gray-800",
    disposed: "bg-red-100 text-red-800",
    lost: "bg-red-100 text-red-800",
    damaged: "bg-orange-100 text-orange-800",
    // License statuses
    active: "bg-green-100 text-green-800",
    expired: "bg-red-100 text-red-800",
    pending_renewal: "bg-yellow-100 text-yellow-800",
    cancelled: "bg-gray-100 text-gray-800",
    // Maintenance priorities
    low: "bg-gray-100 text-gray-700",
    medium: "bg-blue-100 text-blue-700",
    high: "bg-orange-100 text-orange-700",
    critical: "bg-red-100 text-red-700",
  };
  return colors[status] ?? "bg-gray-100 text-gray-700";
}

/**
 * Map condition to a Tailwind CSS color class for badges.
 */
export function getConditionColor(condition: string): string {
  const colors: Record<string, string> = {
    new: "bg-emerald-100 text-emerald-800",
    good: "bg-green-100 text-green-800",
    fair: "bg-yellow-100 text-yellow-800",
    poor: "bg-orange-100 text-orange-800",
    broken: "bg-red-100 text-red-800",
  };
  return colors[condition] ?? "bg-gray-100 text-gray-700";
}

/**
 * Truncate a string to a maximum length, appending ellipsis if needed.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 3) + "...";
}
