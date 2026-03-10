/**
 * Asset list page with filtering, search, and table/grid view toggle.
 */
import { useNavigate } from "react-router-dom";
import DataTable, { type Column } from "../components/DataTable";
import StatusBadge from "../components/StatusBadge";
import { useAssetList, useAssetCategories } from "../hooks/useAssets";
import { useAssetStore } from "../store/assetStore";
import { formatCurrency, formatDate } from "../utils/formatters";
import type { AssetListItem, AssetStatus } from "../types";

const STATUS_OPTIONS: { value: AssetStatus | ""; label: string }[] = [
  { value: "", label: "All Statuses" },
  { value: "available", label: "Available" },
  { value: "assigned", label: "Assigned" },
  { value: "in_maintenance", label: "In Maintenance" },
  { value: "retired", label: "Retired" },
  { value: "disposed", label: "Disposed" },
  { value: "lost", label: "Lost" },
  { value: "damaged", label: "Damaged" },
];

export default function AssetListPage() {
  const navigate = useNavigate();
  const {
    filters,
    setFilter,
    resetFilters,
    setPage,
    selectedAssetIds,
    toggleAssetSelection,
    selectAllAssets,
    clearSelection,
  } = useAssetStore();

  const { data: categories } = useAssetCategories();

  const queryFilters = {
    ...(filters.search && { search: filters.search }),
    ...(filters.status && { status: filters.status }),
    ...(filters.condition && { condition: filters.condition }),
    ...(filters.category && { category: filters.category }),
    ...(filters.asset_type && { asset_type: filters.asset_type }),
    ordering: filters.ordering,
    page: filters.page,
    page_size: filters.page_size,
  };

  const { data, isLoading } = useAssetList(queryFilters);

  const columns: Column<AssetListItem>[] = [
    {
      key: "asset_tag",
      header: "Asset Tag",
      sortable: true,
      render: (row) => (
        <span className="font-medium text-blue-600">{row.asset_tag}</span>
      ),
    },
    {
      key: "name",
      header: "Name",
      sortable: true,
    },
    {
      key: "status",
      header: "Status",
      sortable: true,
      render: (row) => <StatusBadge value={row.status} />,
    },
    {
      key: "condition",
      header: "Condition",
      render: (row) => <StatusBadge value={row.condition} type="condition" />,
    },
    {
      key: "category_name",
      header: "Category",
      render: (row) => row.category_name ?? "-",
    },
    {
      key: "manufacturer",
      header: "Manufacturer",
      render: (row) => row.manufacturer || "-",
    },
    {
      key: "serial_number",
      header: "Serial #",
      render: (row) => row.serial_number || "-",
    },
    {
      key: "location",
      header: "Location",
      render: (row) => row.location || "-",
    },
    {
      key: "purchase_cost",
      header: "Cost",
      sortable: true,
      render: (row) => formatCurrency(row.purchase_cost),
      className: "text-right",
    },
    {
      key: "purchase_date",
      header: "Purchase Date",
      sortable: true,
      render: (row) => formatDate(row.purchase_date),
    },
    {
      key: "current_assignee",
      header: "Assigned To",
      render: (row) => row.current_assignee?.name ?? "-",
    },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Assets</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your organization's IT assets
          </p>
        </div>
        <button
          onClick={() => navigate("/assets/new")}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Add Asset
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border p-4 mb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="Search assets..."
            value={filters.search}
            onChange={(e) => setFilter("search", e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilter("status", e.target.value as AssetStatus | "")}
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            value={filters.category}
            onChange={(e) => setFilter("category", e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Categories</option>
            {categories?.results.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
          <button
            onClick={resetFilters}
            className="border rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Selection toolbar */}
      {selectedAssetIds.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 flex items-center justify-between">
          <span className="text-sm text-blue-700">
            {selectedAssetIds.size} asset(s) selected
          </span>
          <button
            onClick={clearSelection}
            className="text-sm text-blue-600 hover:underline"
          >
            Clear selection
          </button>
        </div>
      )}

      {/* Data table */}
      <div className="bg-white rounded-lg border">
        <DataTable
          columns={columns}
          data={data?.results ?? []}
          isLoading={isLoading}
          emptyMessage="No assets found. Try adjusting your filters."
          selectable
          selectedIds={selectedAssetIds}
          onToggleSelect={toggleAssetSelection}
          onSelectAll={(ids) => selectAllAssets(ids)}
          sortField={filters.ordering.replace("-", "")}
          sortDirection={filters.ordering.startsWith("-") ? "desc" : "asc"}
          onSort={(field) => {
            const currentField = filters.ordering.replace("-", "");
            if (currentField === field) {
              setFilter(
                "ordering",
                filters.ordering.startsWith("-") ? field : `-${field}`,
              );
            } else {
              setFilter("ordering", field);
            }
          }}
          totalCount={data?.count}
          currentPage={filters.page}
          pageSize={filters.page_size}
          onPageChange={setPage}
          onRowClick={(row) => navigate(`/assets/${row.id}`)}
        />
      </div>
    </div>
  );
}
