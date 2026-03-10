/**
 * Generic data table component with sorting, selection, and pagination.
 */
import { clsx } from "clsx";
import type { ReactNode } from "react";

// ---- Column definition ------------------------------------------------------

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render?: (row: T) => ReactNode;
  className?: string;
}

// ---- Component props --------------------------------------------------------

interface DataTableProps<T extends { id: string }> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;

  // Sorting
  sortField?: string;
  sortDirection?: "asc" | "desc";
  onSort?: (field: string) => void;

  // Selection
  selectable?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
  onSelectAll?: (ids: string[]) => void;

  // Pagination
  totalCount?: number;
  currentPage?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;

  // Row click
  onRowClick?: (row: T) => void;
}

export default function DataTable<T extends { id: string }>({
  columns,
  data,
  isLoading = false,
  emptyMessage = "No records found.",
  sortField,
  sortDirection,
  onSort,
  selectable = false,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  totalCount,
  currentPage = 1,
  pageSize = 25,
  onPageChange,
  onRowClick,
}: DataTableProps<T>) {
  const totalPages = totalCount ? Math.ceil(totalCount / pageSize) : 1;

  const allSelected =
    selectable && data.length > 0 && data.every((row) => selectedIds?.has(row.id));

  function handleSelectAll() {
    if (!onSelectAll) return;
    if (allSelected) {
      onSelectAll([]);
    } else {
      onSelectAll(data.map((row) => row.id));
    }
  }

  function renderSortIndicator(field: string) {
    if (sortField !== field) return null;
    return (
      <span className="ml-1 text-xs">
        {sortDirection === "asc" ? "\u25B2" : "\u25BC"}
      </span>
    );
  }

  // ---- Loading skeleton ---------------------------------------------------

  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded mb-2" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-8 bg-gray-100 rounded mb-1" />
        ))}
      </div>
    );
  }

  // ---- Empty state --------------------------------------------------------

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">{emptyMessage}</p>
      </div>
    );
  }

  // ---- Table --------------------------------------------------------------

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {selectable && (
                <th className="w-10 px-3 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300"
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={clsx(
                    "px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    col.sortable && "cursor-pointer select-none hover:text-gray-700",
                    col.className,
                  )}
                  onClick={() => col.sortable && onSort?.(col.key)}
                >
                  {col.header}
                  {col.sortable && renderSortIndicator(col.key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row) => (
              <tr
                key={row.id}
                className={clsx(
                  "transition-colors",
                  onRowClick && "cursor-pointer hover:bg-gray-50",
                  selectedIds?.has(row.id) && "bg-blue-50",
                )}
                onClick={() => onRowClick?.(row)}
              >
                {selectable && (
                  <td
                    className="w-10 px-3 py-3"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      checked={selectedIds?.has(row.id) ?? false}
                      onChange={() => onToggleSelect?.(row.id)}
                      className="rounded border-gray-300"
                    />
                  </td>
                )}
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={clsx(
                      "px-4 py-3 text-sm text-gray-700 whitespace-nowrap",
                      col.className,
                    )}
                  >
                    {col.render
                      ? col.render(row)
                      : String((row as Record<string, unknown>)[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalCount !== undefined && totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Showing {(currentPage - 1) * pageSize + 1} to{" "}
            {Math.min(currentPage * pageSize, totalCount)} of {totalCount} results
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 hover:bg-gray-50"
            >
              Previous
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              let page: number;
              if (totalPages <= 7) {
                page = i + 1;
              } else if (currentPage <= 4) {
                page = i + 1;
              } else if (currentPage >= totalPages - 3) {
                page = totalPages - 6 + i;
              } else {
                page = currentPage - 3 + i;
              }
              return (
                <button
                  key={page}
                  onClick={() => onPageChange(page)}
                  className={clsx(
                    "px-3 py-1 text-sm border rounded",
                    page === currentPage
                      ? "bg-blue-600 text-white border-blue-600"
                      : "hover:bg-gray-50",
                  )}
                >
                  {page}
                </button>
              );
            })}
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
