/**
 * Shared TypeScript type definitions for the AssetGuard frontend.
 */

// ---- Generic ----------------------------------------------------------------

export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ---- Assets -----------------------------------------------------------------

export type AssetStatus =
  | "available"
  | "assigned"
  | "in_maintenance"
  | "retired"
  | "disposed"
  | "lost"
  | "damaged";

export type AssetCondition = "new" | "good" | "fair" | "poor" | "broken";

export interface AssetListItem {
  id: string;
  asset_tag: string;
  name: string;
  status: AssetStatus;
  condition: AssetCondition;
  category_name: string | null;
  type_name: string | null;
  serial_number: string;
  manufacturer: string;
  model_number: string;
  location: string;
  purchase_date: string | null;
  purchase_cost: string;
  current_assignee: {
    employee_id: string;
    name: string;
    checked_out_at: string;
  } | null;
  created_at: string;
}

export interface Asset extends AssetListItem {
  description: string;
  asset_type: string;
  barcode: string;
  purchase_order_number: string;
  vendor: string;
  salvage_value: string;
  building: string;
  floor: string;
  room: string;
  ip_address: string | null;
  mac_address: string;
  hostname: string;
  image: string | null;
  notes: string;
  custom_fields: Record<string, unknown>;
  current_assignment: AssetAssignment | null;
  assignment_history: AssetAssignment[];
  created_by: string | null;
  created_by_name: string | null;
  updated_at: string;
}

export interface AssetCategory {
  id: string;
  name: string;
  description: string;
  parent: string | null;
  is_active: boolean;
  subcategory_count: number;
  asset_type_count: number;
  created_at: string;
}

export interface AssetType {
  id: string;
  name: string;
  category: string;
  category_name: string;
  description: string;
  default_useful_life_months: number;
  is_active: boolean;
  asset_count: number;
  created_at: string;
}

export interface AssetAssignment {
  id: string;
  asset: string;
  asset_tag: string;
  asset_name: string;
  employee: string;
  employee_detail: EmployeeMinimal;
  checked_out_by: string | null;
  checked_out_by_name: string | null;
  checked_out_at: string;
  expected_return_date: string | null;
  notes: string;
  returned_at: string | null;
  checked_in_by: string | null;
  checked_in_by_name: string | null;
  return_condition: string;
  return_notes: string;
  is_active: boolean;
  is_overdue: boolean;
}

// ---- Accounts ---------------------------------------------------------------

export interface EmployeeMinimal {
  id: string;
  employee_id: string;
  full_name: string;
  email: string;
  department: string | null;
}

export interface Employee extends EmployeeMinimal {
  user: string | null;
  first_name: string;
  last_name: string;
  phone: string;
  job_title: string;
  department_name: string | null;
  location: string;
  hire_date: string | null;
  status: "active" | "on_leave" | "terminated";
  is_active: boolean;
  assigned_assets_count: number;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  description: string;
  manager_name: string;
  manager_email: string;
  cost_center: string;
  is_active: boolean;
  employee_count: number;
  asset_count: number;
  created_at: string;
  updated_at: string;
}

// ---- Licenses ---------------------------------------------------------------

export type LicenseType =
  | "per_seat"
  | "per_device"
  | "site"
  | "open_source"
  | "subscription"
  | "perpetual";

export interface SoftwareLicense {
  id: string;
  name: string;
  software_name: string;
  version: string;
  publisher: string;
  license_type: LicenseType;
  status: "active" | "expired" | "pending_renewal" | "cancelled" | "suspended";
  total_seats: number;
  used_seats: number;
  available_seats: number | string;
  expiration_date: string | null;
  days_until_expiration: number | null;
  utilization_percentage: number;
  annual_cost: string;
  purchase_cost: string;
  created_at: string;
}

// ---- Maintenance ------------------------------------------------------------

export interface MaintenanceSchedule {
  id: string;
  asset: string;
  asset_tag: string;
  asset_name: string;
  title: string;
  description: string;
  frequency: string;
  priority: "low" | "medium" | "high" | "critical";
  status: "scheduled" | "in_progress" | "completed" | "cancelled" | "overdue";
  scheduled_date: string;
  scheduled_end_date: string | null;
  completed_date: string | null;
  assigned_to: string;
  vendor: string;
  estimated_cost: string;
  actual_cost: string;
  is_overdue: boolean;
  notes: string;
  created_at: string;
}

// ---- Dashboard --------------------------------------------------------------

export interface DashboardData {
  assets: {
    total: number;
    available: number;
    assigned: number;
    in_maintenance: number;
  };
  assignments: {
    active: number;
    overdue: number;
  };
  licenses: {
    active: number;
    expiring_soon: number;
  };
  maintenance: {
    upcoming: number;
    overdue: number;
  };
}
