/**
 * Dashboard metric card component.
 * Displays a labeled metric value with optional change indicator.
 */
import { clsx } from "clsx";
import type { ReactNode } from "react";

interface DashboardCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    label: string;
    direction: "up" | "down" | "neutral";
  };
  color?: "blue" | "green" | "yellow" | "red" | "gray";
  onClick?: () => void;
  className?: string;
}

const colorStyles: Record<string, { bg: string; icon: string; border: string }> = {
  blue: {
    bg: "bg-blue-50",
    icon: "text-blue-600",
    border: "border-blue-200",
  },
  green: {
    bg: "bg-green-50",
    icon: "text-green-600",
    border: "border-green-200",
  },
  yellow: {
    bg: "bg-yellow-50",
    icon: "text-yellow-600",
    border: "border-yellow-200",
  },
  red: {
    bg: "bg-red-50",
    icon: "text-red-600",
    border: "border-red-200",
  },
  gray: {
    bg: "bg-gray-50",
    icon: "text-gray-600",
    border: "border-gray-200",
  },
};

export default function DashboardCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  color = "blue",
  onClick,
  className,
}: DashboardCardProps) {
  const styles = colorStyles[color];

  return (
    <div
      className={clsx(
        "rounded-lg border p-5 transition-shadow",
        styles.bg,
        styles.border,
        onClick && "cursor-pointer hover:shadow-md",
        className,
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {typeof value === "number" ? value.toLocaleString() : value}
          </p>
          {subtitle && (
            <p className="mt-1 text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className={clsx("text-2xl", styles.icon)}>
            {icon}
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 flex items-center text-xs">
          <span
            className={clsx(
              "font-medium",
              trend.direction === "up" && "text-green-600",
              trend.direction === "down" && "text-red-600",
              trend.direction === "neutral" && "text-gray-500",
            )}
          >
            {trend.direction === "up" && "\u2191 "}
            {trend.direction === "down" && "\u2193 "}
            {trend.value > 0 ? `+${trend.value}` : trend.value}
          </span>
          <span className="ml-1 text-gray-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
