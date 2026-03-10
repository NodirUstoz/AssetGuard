/**
 * Reusable status/condition badge component with color coding.
 */
import { clsx } from "clsx";
import {
  getStatusColor,
  getConditionColor,
  STATUS_LABELS,
  CONDITION_LABELS,
} from "../utils/formatters";

interface StatusBadgeProps {
  value: string;
  type?: "status" | "condition" | "priority";
  className?: string;
}

export default function StatusBadge({
  value,
  type = "status",
  className,
}: StatusBadgeProps) {
  const colorClass =
    type === "condition" ? getConditionColor(value) : getStatusColor(value);

  const labels =
    type === "condition"
      ? CONDITION_LABELS
      : type === "status"
        ? STATUS_LABELS
        : {};

  const label = labels[value] ?? value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        colorClass,
        className,
      )}
    >
      {label}
    </span>
  );
}
