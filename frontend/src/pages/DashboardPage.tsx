/**
 * Dashboard page -- main landing page showing key metrics and charts.
 */
import DashboardCard from "../components/DashboardCard";
import { useDashboard } from "../hooks/useDashboard";
import { useAssetStatusSummary } from "../hooks/useAssets";

export default function DashboardPage() {
  const { data: dashboard, isLoading: dashLoading } = useDashboard();
  const { data: statusSummary, isLoading: statusLoading } = useAssetStatusSummary();

  if (dashLoading || statusLoading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-28 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const d = dashboard!;

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Overview of your IT asset management system
        </p>
      </div>

      {/* Asset metrics */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Assets</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <DashboardCard
          title="Total Assets"
          value={d.assets.total}
          color="blue"
        />
        <DashboardCard
          title="Available"
          value={d.assets.available}
          subtitle={`${d.assets.total > 0 ? ((d.assets.available / d.assets.total) * 100).toFixed(1) : 0}% of total`}
          color="green"
        />
        <DashboardCard
          title="Assigned"
          value={d.assets.assigned}
          color="blue"
        />
        <DashboardCard
          title="In Maintenance"
          value={d.assets.in_maintenance}
          color="yellow"
        />
      </div>

      {/* Assignments */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Assignments</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <DashboardCard
          title="Active Assignments"
          value={d.assignments.active}
          color="blue"
        />
        <DashboardCard
          title="Overdue Returns"
          value={d.assignments.overdue}
          color={d.assignments.overdue > 0 ? "red" : "green"}
        />
      </div>

      {/* Licenses */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Licenses</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <DashboardCard
          title="Active Licenses"
          value={d.licenses.active}
          color="green"
        />
        <DashboardCard
          title="Expiring Soon"
          value={d.licenses.expiring_soon}
          subtitle="Within 30 days"
          color={d.licenses.expiring_soon > 0 ? "yellow" : "green"}
        />
      </div>

      {/* Maintenance */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">Maintenance</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <DashboardCard
          title="Upcoming (14 days)"
          value={d.maintenance.upcoming}
          color="blue"
        />
        <DashboardCard
          title="Overdue"
          value={d.maintenance.overdue}
          color={d.maintenance.overdue > 0 ? "red" : "green"}
        />
      </div>

      {/* Status breakdown chart placeholder */}
      {statusSummary && (
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold text-gray-700 mb-4">
            Asset Status Breakdown
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {Object.entries(statusSummary)
              .filter(([key]) => key !== "total")
              .map(([statusKey, count]) => (
                <div
                  key={statusKey}
                  className="text-center p-3 rounded-lg bg-gray-50"
                >
                  <p className="text-2xl font-bold text-gray-800">{count}</p>
                  <p className="text-xs text-gray-500 mt-1 capitalize">
                    {statusKey.replace(/_/g, " ")}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
